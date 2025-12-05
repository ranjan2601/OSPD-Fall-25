from gemini_impl.client import GeminiClient

def test_extract_tool_calls_returns_empty():
    client = GeminiClient(api_key="dummy")
    result = client.extract_tool_calls("hello world")
    assert result == []
