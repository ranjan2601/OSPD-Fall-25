"""Google Gemini API implementation of AIClient with conversation history storage."""

import sqlite3
from pathlib import Path

from gemini_api import AIClient, Message


class GeminiClient(AIClient):
    """Concrete implementation using Google Gemini API.

    Attributes:
        api_key: Google Gemini API key for authentication.
        db_path: Path to SQLite database for storing conversation history.

    """

    def __init__(self, api_key: str, db_path: str = "conversations.db") -> None:
        """Initialize the Gemini client.

        Args:
            api_key: Google Gemini API key.
            db_path: Path to SQLite database file. Defaults to "conversations.db".

        Raises:
            ValueError: If api_key is empty.

        """
        if not api_key:
            msg = "api_key cannot be empty"
            raise ValueError(msg)

        self.api_key = api_key
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database for conversation storage."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_id ON conversations(user_id)",
            )
            conn.commit()

    def send_message(self, user_id: str, message: str) -> str:
        """Send a message and get a response from Gemini API.

        Args:
            user_id: Unique identifier for the user.
            message: The message text to send.

        Returns:
            The AI's response as a string.

        Raises:
            ValueError: If user_id or message is empty.
            RuntimeError: If there's an error with the Gemini API.

        """
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)
        if not message:
            msg = "message cannot be empty"
            raise ValueError(msg)

        # Store user message
        self._store_message(user_id, "user", message)

        # Generate response (would call Gemini API in production)
        response = self._generate_response(message)

        # Store assistant response
        self._store_message(user_id, "assistant", response)

        return response

    def _generate_response(self, message: str) -> str:
        """Generate a response for the message.

        In production, this would call the Gemini API using:
        `import google.generativeai as genai` and
        `model = genai.GenerativeModel("gemini-pro")`.

        For now, returns a placeholder response.

        Args:
            message: The user's message.

        Returns:
            A response string.

        """
        return f"Response to: {message}"

    def get_conversation_history(self, user_id: str) -> list[Message]:
        """Retrieve the conversation history for a user.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            A list of Message objects representing the conversation history.

        Raises:
            ValueError: If user_id is empty.

        """
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)

        messages: list[Message] = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY created_at ASC",
                (user_id,),
            )
            rows = cursor.fetchall()

        for role, content in rows:
            messages.append(Message(role=role, content=content))

        return messages

    def clear_conversation(self, user_id: str) -> bool:
        """Clear the conversation history for a user.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            True if the conversation was successfully cleared, False otherwise.

        Raises:
            ValueError: If user_id is empty.

        """
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def _store_message(self, user_id: str, role: str, content: str) -> None:
        """Store a message in the database.

        Args:
            user_id: Unique identifier for the user.
            role: Role of the message sender ("user" or "assistant").
            content: The message content.

        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content),
            )
            conn.commit()
