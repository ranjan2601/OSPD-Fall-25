import sys
from pathlib import Path

# Add the mail_client_api to Python path
mail_client_api_path = Path(__file__).parent.parent / "mail_client_api/src"
sys.path.append(str(mail_client_api_path))

# Now import
from mail_client_api import get_client

try:
    client = get_client(interactive=True)
    messages = list(client.get_messages(max_results=5))
    for _msg in messages:
        pass
except Exception:
    pass
