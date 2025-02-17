import requests
from config import Config

class JiraAssetsClient:
    def __init__(self):
        self.base_url = Config.JIRA_URL
        self.auth = (Config.JIRA_USER, Config.JIRA_API_TOKEN)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def get_all_assets(self):
        """Get all assets from Jira Assets"""
        endpoint = f"{self.base_url}/rest/assets/1.0/assets"
        response = requests.get(endpoint, auth=self.auth, headers=self.headers)
        return response.json()

    def get_asset_by_id(self, asset_id):
        """Get specific asset by ID"""
        endpoint = f"{self.base_url}/rest/assets/1.0/assets/{asset_id}"
        response = requests.get(endpoint, auth=self.auth, headers=self.headers)
        return response.json()
