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
    print(f"Successfully retrieved {len(messages)} messages!")
    for msg in messages:
        print(f"- {msg.subject} from {msg.from_}")
except Exception as e:
    print(f"Error: {e}")