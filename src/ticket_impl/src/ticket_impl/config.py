"""Runtime settings for Jira Cloud + OAuth."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)


class Settings(BaseModel):
    """Container for environment-based configuration."""

    # Jira Cloud
    jira_cloud_id: str = os.environ.get("JIRA_CLOUD_ID", "dummy-cloud-id-for-development")
    jira_api_base: str = os.environ.get(
        "JIRA_API_BASE",
        f"https://api.atlassian.com/ex/jira/{os.environ.get('JIRA_CLOUD_ID', 'dummy-cloud-id-for-development')}",
    )

    # Atlassian OAuth 2.0 (3LO)
    oauth_client_id: str = os.environ.get("OAUTH_CLIENT_ID", "dummy-client-id")
    oauth_client_secret: str = os.environ.get("OAUTH_CLIENT_SECRET", "dummy-client-secret")
    oauth_redirect_uri: str = os.environ.get("OAUTH_REDIRECT_URI", "http://127.0.0.1:8000/api/v1/auth/callback")

    # Token & mapping DB
    db_url: str = os.environ.get("DB_URL", "sqlite:///./jira_tokens.db")


settings = Settings()
