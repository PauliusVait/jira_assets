# Jira Assets API Client

A Python client for interacting with the Jira Assets REST API, with support for rate limiting and mass updates.

## Setup

1. Clone the repository
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your Jira credentials:
   ```env
   JIRA_URL=https://your-domain.atlassian.net
   JIRA_USER=your-email@example.com
   JIRA_API_TOKEN=your-api-token
   ```

## Usage

### Command Line Interface

The tool provides several commands:

```bash
# Get a single asset
python main.py get --id <asset_id> [--debug]

# Update a single asset
python main.py update --id <asset_id> [--attrs NAME=value,COST=100] [--debug]

# Mass update assets of specific type
python main.py mass-update --type 442 [--workers 5] [--debug]

# Run AQL query
python main.py query --query "objectTypeId = 442" [--debug]
```

### Asset Types

- Computers (442)
- Phones (443)
- Tablets (475)

### Rate Limiting

The client automatically handles rate limiting with exponential backoff. Default settings:
- Max retries: 5
- Initial delay: 1 second
- Maximum delay: 32 seconds

### Logging

Logs are stored in the `logs/` directory with timestamps. Use `--debug` flag for detailed API interaction logs.

## Development

### Project Structure
```
jira_assets/
├── main.py           # CLI interface
├── jira_client.py    # Main client implementation
├── jira_api.py       # API interaction layer
├── config.py         # Configuration management
└── buyout_calculator.py  # Business logic for calculations
```
