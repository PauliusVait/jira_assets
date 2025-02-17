# Jira Assets API Client

A Python client for interacting with the Jira Assets REST API.

## Setup

1. Clone the repository
2. Create and activate virtual environment:
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your Jira credentials:
   ```
   JIRA_URL=https://your-domain.atlassian.net
   JIRA_USER=your-email@example.com
   JIRA_API_TOKEN=your-api-token
   ```

## Usage

Basic usage example:

```python
from jira_client import JiraAssetsClient

client = JiraAssetsClient()
assets = client.get_all_assets()
```

## Available Methods

- `get_all_assets()`: Retrieve all assets
- `get_asset_by_id(asset_id)`: Retrieve a specific asset by ID
