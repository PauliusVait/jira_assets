from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
    JIRA_USER = os.getenv('JIRA_USER')
    WORKSPACE_ID = "b9ccd491-3d1f-4192-bae1-80c8fc76a741"
