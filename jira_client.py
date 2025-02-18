import requests
from config import Config
import logging
from typing import Dict, Any
from buyout_calculator import update_asset_calculations
from jira_api import JiraAPI
import concurrent.futures
from queue import Queue
import threading
from collections import deque
from time import sleep

class ObjectTypes:
    """Constants for object type IDs"""
    COMPUTERS = "442"
    PHONES = "443"
    TABLETS = "475"

class AssetAttributes:
    """Asset attribute IDs mapped by object type"""
    # Computers (442) attributes
    COMPUTERS = {
        "NAME": "4967",
        "SERIAL_NUMBER": "2896",
        "MODEL": "2902",
        "ORIGINAL_COST": "5004",
        "COST_WITH_VAT": "5005",
        "BUYOUT_PRICE": "5006",
        "PURCHASE_DATE": "5007",
        "DEVICE_AGE": "5035"
    }
    
    # Phones (443) attributes
    PHONES = {
        "NAME": "3936",
        "SERIAL_NUMBER": "2932",
        "MODEL": "3928",
        "ORIGINAL_COST": "5009",
        "COST_WITH_VAT": "5010",
        "BUYOUT_PRICE": "5011",
        "PURCHASE_DATE": "5012",
        "DEVICE_AGE": "5036"
    }
    
    # Tablets (475) attributes
    TABLETS = {
        "NAME": "3937",
        "SERIAL_NUMBER": "3126",
        "MODEL": "3932",  
        "ORIGINAL_COST": "5014",
        "COST_WITH_VAT": "5015",
        "BUYOUT_PRICE": "5016",
        "PURCHASE_DATE": "4077",
        "DEVICE_AGE": "5037"
    }

class JiraAssetsClient:
    def __init__(self):
        self.api = JiraAPI()
        self.log_queue = Queue()
        self.log_buffer = deque(maxlen=100)  # Buffer for batch logging
        self._setup_logging_thread()

    def _setup_logging_thread(self):
        """Setup background thread for batch logging"""
        def log_worker():
            while True:
                try:
                    messages = []
                    # Wait for first message
                    messages.append(self.log_queue.get())
                    
                    # Collect any other pending messages
                    while not self.log_queue.empty() and len(messages) < 100:
                        messages.append(self.log_queue.get())
                    
                    # Log messages in batch
                    for msg in messages:
                        logging.info(msg)
                    
                    sleep(0.1)  # Small delay to prevent CPU overuse
                except Exception as e:
                    logging.error(f"Error in logging thread: {e}")

        thread = threading.Thread(target=log_worker, daemon=True)
        thread.start()

    def _batch_log(self, message: str):
        """Add message to logging queue"""
        self.log_queue.put(message)

    def _process_single_asset(self, asset: Dict) -> Dict[str, Any]:
        """Process a single asset update with error handling"""
        try:
            asset_id = asset.get('id')
            if not asset_id:
                return {"status": "skipped", "reason": "no_id"}

            # Check if we have object type info in the search results
            asset_type = asset.get('objectType', {}).get('id')
            if not asset_type:
                self._batch_log(f"Warning: Asset {asset_id} missing object type in search results")
            
            self._batch_log(f"Processing asset {asset_id} (Type: {asset_type})")
            result = self.auto_update_calculations(asset_id)
            
            if result:
                return {"status": "updated", "id": asset_id}
            else:
                return {"status": "failed", "id": asset_id, "reason": "update_failed"}
                
        except Exception as e:
            return {"status": "error", "id": asset.get('id'), "reason": str(e)}

    def _get_attribute_ids(self, object_type_id: str) -> Dict[str, str]:
        """Get the correct attribute IDs for the given object type"""
        if object_type_id == ObjectTypes.COMPUTERS:
            return AssetAttributes.COMPUTERS
        elif object_type_id == ObjectTypes.PHONES:
            return AssetAttributes.PHONES
        elif object_type_id == ObjectTypes.TABLETS:
            return AssetAttributes.TABLETS
        return AssetAttributes.COMPUTERS  # Default to computers if type not found

    def _extract_attribute_value(self, attributes: list, attribute_id: str) -> str:
        """Extract value for a specific attribute ID from attributes list"""
        for attr in attributes:
            if attr.get('objectTypeAttributeId') == attribute_id:
                values = attr.get('objectAttributeValues', [])
                if values:
                    return values[0].get('value', '')
        return ''

    def search_assets_by_aql(self, aql_query, start_at=0, max_results=50, include_attributes=True):
        """Search assets using AQL (Asset Query Language) and handle pagination"""
        all_values = []
        current_start = start_at
        
        while True:
            result = self.api.search_objects(aql_query, current_start, max_results, include_attributes)
            
            # Add values from current page to our collection
            if 'values' in result:
                all_values.extend(result['values'])
                logging.info(f"Retrieved {len(result['values'])} assets. Total so far: {len(all_values)}")
            
            # Check if we've got all results
            if not result.get('values') or len(result['values']) < max_results:
                break
                
            current_start += max_results
        
        return {
            'startAt': start_at,
            'maxResults': max_results,
            'total': len(all_values),
            'values': all_values
        }

    def get_asset_by_object_id(self, object_id: str) -> Dict[str, Any]:
        """Get specific attributes of an asset by its object ID"""
        full_asset = self.api.get_object(object_id)
        
        if not full_asset:
            logging.error(f"Could not retrieve asset {object_id}")
            return None
            
        # Get object type ID from the response
        object_type = full_asset.get('objectType', {})
        object_type_id = object_type.get('id')
        if not object_type_id:
            logging.error(f"Asset {object_id} missing object type. Full object type data: {object_type}")
            return None

        # Get the correct attribute IDs for this object type
        attribute_ids = self._get_attribute_ids(object_type_id)
        
        # Extract attributes using the correct IDs for this object type
        attributes = full_asset.get('attributes', [])
        asset_data = {
            'id': object_id,
            'object_type': object_type_id,
            'object_type_name': object_type.get('name', ''),
            'object_schema': object_type.get('schema', ''),  # Add schema info for debugging
            'name': self._extract_attribute_value(attributes, attribute_ids['NAME']),
            'serial_number': self._extract_attribute_value(attributes, attribute_ids['SERIAL_NUMBER']),
            'model': self._extract_attribute_value(attributes, attribute_ids['MODEL']),
            'original_cost': self._extract_attribute_value(attributes, attribute_ids['ORIGINAL_COST']),
            'cost_with_vat': self._extract_attribute_value(attributes, attribute_ids['COST_WITH_VAT']),
            'buyout_price': self._extract_attribute_value(attributes, attribute_ids['BUYOUT_PRICE']),
            'purchase_date': self._extract_attribute_value(attributes, attribute_ids['PURCHASE_DATE'])
        }
        
        return update_asset_calculations(asset_data)

    def _prepare_attribute_update(self, attribute_id: str, value: str) -> Dict:
        """Prepare attribute update structure"""
        return {
            "objectTypeAttributeId": attribute_id,
            "objectAttributeValues": [{"value": value}]
        }

    def update_asset(self, object_id: str, updates: Dict[str, str]) -> Dict[str, Any]:
        """Update asset attributes"""
        # First get the current asset to determine its type
        asset = self.get_asset_by_object_id(object_id)
        if not asset:
            logging.error(f"Could not retrieve asset {object_id} for update")
            return None
            
        # Get attribute IDs for this object type
        attribute_ids = self._get_attribute_ids(asset['object_type'])
        
        # Prepare attributes for update
        attributes_to_update = []
        for attr_name, new_value in updates.items():
            if attr_name in attribute_ids:
                attr_update = self._prepare_attribute_update(attribute_ids[attr_name], new_value)
                attributes_to_update.append(attr_update)
                logging.debug(f"Will update {attr_name} to {new_value} using ID {attribute_ids[attr_name]}")
            else:
                logging.warning(f"Unknown attribute {attr_name} for object type {asset['object_type_name']}")
        
        if not attributes_to_update:
            logging.error("No valid attributes to update")
            return None
            
        # Log the update attempt
        logging.info(f"Attempting to update asset {object_id} with {len(attributes_to_update)} attributes")
        
        # Perform update
        updated_asset = self.api.update_object(
            object_id,
            asset['object_type'],
            attributes_to_update
        )
        
        if not updated_asset:
            logging.error(f"Update failed for asset {object_id}")
            return None
            
        # Get and verify the new state
        new_state = self.get_asset_by_object_id(object_id)
        if new_state:
            # Verify updates were applied
            success = all(
                new_state.get(attr) == value 
                for attr, value in updates.items() 
                if attr in new_state
            )
            if success:
                logging.info(f"Successfully verified updates for asset {object_id}")
            else:
                logging.warning(f"Updates may not have been applied correctly for asset {object_id}")
        
        return new_state

    def _validate_name_update(self, asset: Dict[str, Any]) -> tuple[bool, str]:
        """Validate if asset has required attributes for name update"""
        required_attrs = {
            'model': 'Model',
            'serial_number': 'Serial Number'
        }
        
        missing = [label for attr, label in required_attrs.items() 
                  if not asset.get(attr)]
        
        if missing:
            return False, f"Missing required attributes for name update: {', '.join(missing)}"
            
        return True, ""

    def _validate_buyout_calculation(self, asset: Dict[str, Any]) -> tuple[bool, str]:
        """Validate if asset has required attributes for buyout calculation"""
        required_attrs = {
            'original_cost': 'Original Cost',
            'purchase_date': 'Purchase Date'
        }
        
        missing = [label for attr, label in required_attrs.items() 
                  if not asset.get(attr)]
        
        if missing:
            return False, f"Missing required attributes for buyout calculation: {', '.join(missing)}"
            
        return True, ""

    def _validate_device_age(self, asset: Dict[str, Any]) -> tuple[bool, str]:
        """Validate if asset has purchase date for age calculation"""
        if not asset.get('purchase_date'):
            return False, "Missing purchase date for device age calculation"
        return True, ""

    def _format_asset_name(self, asset: Dict[str, Any]) -> str:
        """Format asset name according to business rules"""
        if not all([asset.get('model'), asset.get('serial_number')]):
            logging.warning("Cannot format asset name: missing model or serial number")
            return ""
        
        # Basic name format
        name = f"{asset['model']} - {asset['serial_number']}"
        
        # Add buyout price only if device is older than 18 months
        if asset.get('age_months', 0) > 18 and asset.get('buyout_price'):
            name += f", Buyout Price (€{asset['buyout_price']})"
            
        return name

    def auto_update_calculations(self, object_id: str) -> Dict[str, Any]:
        """Automatically update calculated fields if they need updating"""
        # Get current asset state
        current_asset = self.get_asset_by_object_id(object_id)
        if not current_asset:
            return None
            
        updates_needed = {}
        
        # Check if we can update the name
        can_update_name, name_error = self._validate_name_update(current_asset)
        if can_update_name:
            new_name = self._format_asset_name(current_asset)
            if new_name:
                updates_needed['NAME'] = new_name
        else:
            logging.warning(f"Skipping name update: {name_error}")
        
        # Always try to update device age if purchase date is available
        can_update_age, age_error = self._validate_device_age(current_asset)
        if can_update_age:
            calculated = update_asset_calculations(current_asset.copy())
            if calculated.get('age_months'):
                updates_needed['DEVICE_AGE'] = str(calculated['age_months'])
        else:
            logging.warning(f"Skipping device age update: {age_error}")
        
        # Check if we can do buyout calculations
        can_calculate, calc_error = self._validate_buyout_calculation(current_asset)
        if can_calculate:
            # Use already calculated values if available, otherwise calculate fresh
            calculated = calculated if 'calculated' in locals() else update_asset_calculations(current_asset.copy())
            
            if calculated.get('cost_with_vat'):
                updates_needed['COST_WITH_VAT'] = calculated['cost_with_vat']
                
            if calculated.get('buyout_price'):
                updates_needed['BUYOUT_PRICE'] = calculated['buyout_price']
                
            # Update name again if buyout price should be included
            if can_update_name and calculated.get('age_months', 0) > 18:
                new_name = self._format_asset_name(calculated)
                if new_name:
                    updates_needed['NAME'] = new_name
        else:
            logging.warning(f"Skipping buyout calculations: {calc_error}")
        
        # If updates are needed, perform them
        if updates_needed:
            logging.info(f"Updates needed for asset {object_id}: {updates_needed}")
            return self.update_asset(object_id, updates_needed)
        
        logging.info(f"No updates needed for asset {object_id}")
        return current_asset

    def mass_update_assets(self, object_type: str = None, max_workers: int = 5) -> Dict[str, Any]:
        """Mass update assets using parallel processing"""
        # Get object type mapping for the query
        object_type_mapping = {
            "442": "Computers",
            "443": "Phones",
            "475": "Tablets"
        }
        
        # Construct AQL query based on object type
        if object_type:
            query = f'objectTypeId = {object_type}'
        else:
            # Explicitly list the object types we support
            query = 'objectTypeId in (442, 443, 475)'
            
        logging.info(f"Executing query: {query}")
        
        # Get all matching assets with additional type info
        results = self.search_assets_by_aql(
            query,
            include_attributes=True,
            max_results=50  # Keep batch size reasonable
        )
        
        if not results.get('values'):
            type_name = object_type_mapping.get(object_type, "specified type") if object_type else "any type"
            self._batch_log(f"No assets found of {type_name}")
            return {"total": 0, "updated": 0, "failed": 0, "skipped": 0, "errors": []}
        
        assets = results['values']
        total = len(assets)
        self._batch_log(f"Starting mass update of {total} assets...")
        
        # Process assets in parallel
        stats = {"updated": 0, "failed": 0, "skipped": 0}
        processed = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all assets for processing
            future_to_asset = {
                executor.submit(self._process_single_asset, asset): asset 
                for asset in assets
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_asset):
                result = future.result()
                status = result.get('status')
                
                if status == "updated":
                    stats["updated"] += 1
                elif status == "failed":
                    stats["failed"] += 1
                else:
                    stats["skipped"] += 1
                
                processed += 1
                if processed % 10 == 0:  # Log progress every 10 assets
                    self._batch_log(f"Progress: {processed}/{total} assets processed")
        
        stats["total"] = total
        self._batch_log(f"Mass update completed: {stats}")
        return stats
