from jira_client import JiraAssetsClient

def main():
    client = JiraAssetsClient()
    
    # Example: Get all assets
    assets = client.get_all_assets()
    print("All assets:", assets)
    
    # Example: Get specific asset
    asset_id = "ABC-123"  # Replace with actual asset ID
    asset = client.get_asset_by_id(asset_id)
    print(f"Asset {asset_id}:", asset)

if __name__ == "__main__":
    main()
