"""Google Gemini API implementation of AIClient with conversation history storage."""

import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import google.generativeai as genai
from gemini_api import AIClient, Message


class GeminiClient(AIClient):
    """Concrete implementation using Google Gemini API.

    Attributes:
        api_key: Google Gemini API key for authentication.
        db_path: Path to SQLite database for storing conversation history.
        _request_times: List of request timestamps for rate limiting.
        _daily_request_count: Count of requests made today.
        _last_reset_date: Date when daily count was last reset.

    """

    # Rate limiting constants
    REQUESTS_PER_MINUTE = 4  # Conservative limit for free tier
    REQUESTS_PER_DAY = 180  # Conservative limit (200 - safety margin)
    MIN_DELAY_BETWEEN_REQUESTS = 15  # seconds

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

        # Initialize rate limiting tracking
        self._request_times: list[float] = []
        self._daily_request_count = 0
        self._last_reset_date = datetime.now().date()

        # Initialize Gemini API
        genai.configure(api_key=api_key)  # type: ignore[attr-defined]
        self.model: Any = genai.GenerativeModel("gemini-2.0-flash")  # type: ignore[attr-defined]

        self._init_db()

    def _check_rate_limits(self) -> None:
        """Check and enforce rate limits before making API calls.

        Raises:
            RuntimeError: If daily or per-minute rate limits are exceeded.

        """
        # Reset daily counter if it's a new day
        today = datetime.now().date()
        if today > self._last_reset_date:
            self._daily_request_count = 0
            self._request_times.clear()
            self._last_reset_date = today

        # Check daily limit
        if self._daily_request_count >= self.REQUESTS_PER_DAY:
            msg = (
                f"Daily API quota exceeded ({self._daily_request_count}/"
                f"{self.REQUESTS_PER_DAY}). "
                "Please try again tomorrow."
            )
            raise RuntimeError(msg)

        # Check per-minute limit
        now = time.time()
        # Remove requests older than 60 seconds
        self._request_times = [t for t in self._request_times if now - t < 60]

        if len(self._request_times) >= self.REQUESTS_PER_MINUTE:
            oldest_request = self._request_times[0]
            wait_time = 60 - (now - oldest_request)
            msg = (
                f"Per-minute rate limit would be exceeded. "
                f"Please wait {wait_time:.1f} seconds before retrying."
            )
            raise RuntimeError(msg)

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting after an API call."""
        # Update tracking
        self._daily_request_count += 1
        self._request_times.append(time.time())

        # Apply minimum delay between requests
        time.sleep(self.MIN_DELAY_BETWEEN_REQUESTS)

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
        """Generate a response for the message using Gemini API.

        Args:
            message: The user's message.

        Returns:
            A response string from Gemini API.

        Raises:
            RuntimeError: If there's an error calling the Gemini API or rate limits exceeded.

        """
        # Check rate limits before making API call
        self._check_rate_limits()

        try:
            response = self.model.generate_content(message)
        except Exception as e:
            msg = f"Error calling Gemini API: {e!s}"
            raise RuntimeError(msg) from e
        else:
            # Apply rate limiting (includes 15-second delay between requests)
            self._apply_rate_limit()
            return response.text  # type: ignore[no-any-return]

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
