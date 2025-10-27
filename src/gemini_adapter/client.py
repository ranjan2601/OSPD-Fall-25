from gemini_api import GeminiClient  # your abstract base interface
from gemini_service_api_client.gemini_ai_service_client import Client as GeminiHTTPClient


class GeminiServiceClient(GeminiClient):
    """Adapter that connects the abstract Gemini API to the FastAPI Gemini service."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.client = GeminiHTTPClient(base_url=base_url)

    def send_message(self, user_id: str, message: str) -> str:
        """Send a message via the Gemini FastAPI service."""
        response = self.client.send_message_chat_post(
            json_body={"user_id": user_id, "message": message}
        )
        return response.response
