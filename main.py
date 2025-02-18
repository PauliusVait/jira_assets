from jira_client import JiraAssetsClient
import json
import argparse
import logging
from datetime import datetime
import os
from typing import Dict

def setup_logging(debug: bool = False):
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Generate timestamp for the log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/aql_query_{timestamp}.log'
    
    # Set log level based on debug flag
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return log_file

def run_aql_query(query=None, start_at=0, max_results=50, debug=False):
    log_file = setup_logging(debug)
    
    if not query:
        # Default query if none provided
        query = 'objecttype in ("Computers", "Phones", "Tablets") AND Status not in ("Inactive") AND Model is not EMPTY'
    
    logging.info(f"Executing query: {query}")
    logging.info(f"Starting asset retrieval (this might take a while for large datasets)...")
    
    client = JiraAssetsClient()
    results = client.search_assets_by_aql(query, start_at, max_results)
    
    # Log the results
    logging.info("Query completed!")
    logging.info(f"Final results - Total assets retrieved: {len(results['values'])}")
    logging.info(json.dumps(results, indent=2))
    
    # Print summary
    if 'values' in results:
        summary = f"\nTotal results found: {len(results['values'])}"
        logging.info(summary)
        print(f"\nResults have been saved to: {log_file}")

def run_get_asset(object_id: str, debug: bool = False):
    """Run get asset operation"""
    log_file = setup_logging(debug)
    
    logging.info(f"Retrieving asset with ID: {object_id}")
    
    client = JiraAssetsClient()
    result = client.get_asset_by_object_id(object_id)
    
    if result:
        logging.info("Asset found:")
        logging.info(json.dumps(result, indent=2))
    else:
        logging.error("Asset not found")
    
    print(f"\nResults have been saved to: {log_file}")

def run_update_asset(object_id: str, updates: Dict[str, str] = None, debug: bool = False):
    """Run asset update operation"""
    log_file = setup_logging(debug)
    
    logging.info(f"Checking asset {object_id} for needed updates")
    
    client = JiraAssetsClient()
    
    if updates:
        # Manual update with provided values
        logging.info(f"Performing manual update with values: {updates}")
        result = client.update_asset(object_id, updates)
    else:
        # Automatic update of calculated values
        logging.info("Performing automatic update of calculated values")
        result = client.auto_update_calculations(object_id)
    
    if result:
        logging.info("Asset processing completed:")
        logging.info(json.dumps(result, indent=2))
    else:
        logging.error("Failed to process asset")
    
    print(f"\nResults have been saved to: {log_file}")

def run_mass_update(object_type: str = None, workers: int = 10, debug: bool = False):
    """Run mass update operation"""
    log_file = setup_logging(debug)
    
    if object_type:
        logging.info(f"Starting mass update for object type: {object_type}")
    else:
        logging.info("Starting mass update for all asset types")
    
    client = JiraAssetsClient()
    results = client.mass_update_assets(object_type)
    
    logging.info("Mass update completed:")
    logging.info(json.dumps(results, indent=2))
    print(f"\nResults have been saved to: {log_file}")

def main():
    parser = argparse.ArgumentParser(description='Run Jira Assets API operations')
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # AQL query parser
    query_parser = subparsers.add_parser('query', help='Run AQL query')
    query_parser.add_argument('--query', '-q', help='AQL query to run')
    query_parser.add_argument('--start', '-s', type=int, default=0, help='Start at position')
    query_parser.add_argument('--limit', '-l', type=int, default=50, help='Maximum results to return')
    query_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    # Get asset parser
    get_parser = subparsers.add_parser('get', help='Get asset by ID')
    get_parser.add_argument('--id', required=True, help='Object ID of the asset')
    get_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    # Update asset parser
    update_parser = subparsers.add_parser('update', help='Update asset attributes')
    update_parser.add_argument('--id', required=True, help='Object ID of the asset')
    update_parser.add_argument('--attrs', '-a', help='Optional: Attributes to update in format: ATTR1=value1,ATTR2=value2')
    update_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    # Mass update parser
    mass_parser = subparsers.add_parser('mass-update', help='Mass update assets')
    mass_parser.add_argument('--type', '-t', choices=['442', '443', '475'], 
                           help='Optional: Object type to update (442=Computers, 443=Phones, 475=Tablets)')
    mass_parser.add_argument('--workers', '-w', type=int, default=10,
                           help='Number of worker threads (default: 10)')
    mass_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.command == 'mass-update':
        run_mass_update(args.type, args.workers, args.debug)
    elif args.command == 'query':
        run_aql_query(args.query, args.start, args.limit, args.debug)
    elif args.command == 'get':
        run_get_asset(args.id, args.debug)
    elif args.command == 'update':
        updates = dict(item.split("=") for item in args.attrs.split(",")) if args.attrs else None
        run_update_asset(args.id, updates, args.debug)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
