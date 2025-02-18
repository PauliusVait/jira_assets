import requests
import logging
from typing import Dict, Any, List, Optional
from config import Config
from functools import lru_cache
from time import time, sleep
import json
from datetime import datetime
import random

class RateLimitError(Exception):
    """Custom exception for rate limiting"""
    def __init__(self, retry_after: int, reset_time: Optional[str] = None):
        self.retry_after = retry_after
        self.reset_time = reset_time
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")

class JiraAPI:
    def __init__(self):
        self.base_url = Config.JIRA_URL
        self.auth = (Config.JIRA_USER, Config.JIRA_API_TOKEN)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self._cache_timeout = 300  # 5 minutes cache timeout
        self._cache_timestamp = {}
        self.max_retries = 5
        self.initial_delay = 1  # Start with 1 second delay
        self.max_delay = 32  # Maximum delay in seconds

    @lru_cache(maxsize=1000)
    def _get_object_cached(self, object_id: str) -> Dict[str, Any]:
        """Cached version of get_object"""
        response = requests.get(
            f"https://api.atlassian.com/jsm/assets/workspace/{Config.WORKSPACE_ID}/v1/object/{object_id}",
            headers=self.headers,
            auth=self.auth
        )
        
        if response.status_code == 404:
            return None
            
        return response.json()

    def _handle_rate_limit(self, response: requests.Response) -> int:
        """Handle rate limit response and return retry delay"""
        retry_after = int(response.headers.get('Retry-After', self.initial_delay))
        reset_time = response.headers.get('X-RateLimit-Reset')
        
        if reset_time:
            logging.warning(f"Rate limit will reset at: {reset_time}")
        
        raise RateLimitError(retry_after, reset_time)

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with rate limit handling and exponential backoff"""
        current_retry = 0
        current_delay = self.initial_delay
        
        while current_retry <= self.max_retries:
            try:
                response = requests.request(method, url, **kwargs)
                
                # Check for rate limit
                if response.status_code == 429:
                    retry_delay = self._handle_rate_limit(response)
                    current_delay = min(retry_delay, self.max_delay)
                elif response.status_code >= 500:
                    # Handle server errors with backoff
                    if 'Retry-After' in response.headers:
                        current_delay = int(response.headers['Retry-After'])
                    else:
                        current_delay = min(current_delay * 2, self.max_delay)
                else:
                    # Check if we're approaching the rate limit
                    if response.headers.get('X-RateLimit-NearLimit') == 'true':
                        logging.warning("Approaching rate limit, adding delay to subsequent requests")
                        sleep(1)  # Add small delay to help avoid hitting limit
                    return response
                
                # Add jitter to avoid thundering herd
                jitter = random.uniform(0, 0.1) * current_delay
                sleep_time = current_delay + jitter
                
                logging.warning(f"Request failed, retrying in {sleep_time:.2f} seconds (attempt {current_retry + 1}/{self.max_retries})")
                sleep(sleep_time)
                
                current_retry += 1
                
            except RateLimitError as e:
                if current_retry >= self.max_retries:
                    raise
                sleep(e.retry_after)
                current_retry += 1
            except Exception as e:
                logging.error(f"Request failed: {str(e)}")
                raise

        raise Exception(f"Max retries ({self.max_retries}) exceeded")

    def get_object(self, object_id: str) -> Dict[str, Any]:
        """Get object with rate limit handling"""
        try:
            # Check cache first
            if object_id in self._cache_timestamp:
                if time() - self._cache_timestamp[object_id] > self._cache_timeout:
                    self._get_object_cached.cache_clear()
            
            url = f"https://api.atlassian.com/jsm/assets/workspace/{Config.WORKSPACE_ID}/v1/object/{object_id}"
            response = self._make_request('get', url, headers=self.headers, auth=self.auth)
            
            if response.status_code == 404:
                return None
                
            result = response.json()
            self._cache_timestamp[object_id] = time()
            
            if not result.get('objectType', {}).get('id'):
                logging.error(f"API response missing object type for asset {object_id}. Response: {result}")
                return None
                
            return result
            
        except Exception as e:
            logging.error(f"Error retrieving asset {object_id}: {str(e)}")
            return None

    def search_objects(self, aql_query: str, start_at: int = 0, max_results: int = 50, include_attributes: bool = True) -> Dict:
        """Execute AQL search request"""
        endpoint = f"https://api.atlassian.com/jsm/assets/workspace/{Config.WORKSPACE_ID}/v1/object/aql"
        
        params = {
            'startAt': start_at,
            'maxResults': max_results,
            'includeAttributes': str(include_attributes).lower()
        }
        
        payload = {
            "qlQuery": aql_query
        }
        
        response = self._make_request(
            'post',
            endpoint,
            params=params,
            json=payload,
            headers=self.headers,
            auth=self.auth
        )
        return response.json()

    def update_object(self, object_id: str, object_type_id: str, attributes: List[Dict]) -> Dict[str, Any]:
        """Update object attributes with rate limit handling"""
        endpoint = f"https://api.atlassian.com/jsm/assets/workspace/{Config.WORKSPACE_ID}/v1/object/{object_id}"
        
        payload = {
            "attributes": attributes,
            "objectTypeId": object_type_id,
            "avatarUUID": "",
            "hasAvatar": False
        }
        
        logging.debug(f"Making PUT request to {endpoint}")
        logging.debug(f"Update payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = self._make_request(
                'put',
                endpoint,
                json=payload,
                headers=self.headers,
                auth=self.auth
            )
            
            logging.debug(f"API Response status: {response.status_code}")
            logging.debug(f"API Response headers: {dict(response.headers)}")
            
            if response.status_code not in [200, 201]:
                logging.error(f"Failed to update asset {object_id}: {response.text}")
                return None
            
            logging.info(f"Successfully updated asset {object_id}")
            return response.json()
            
        except Exception as e:
            logging.error(f"Exception during API update: {str(e)}")
            return None
