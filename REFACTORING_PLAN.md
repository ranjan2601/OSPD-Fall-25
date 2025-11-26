# Refactoring Plan: Proper Dependency Injection for AI Client

## Overview
Implement proper dependency injection pattern following the mail_client_api model, where implementations register themselves when imported.

## Changes Required

### 1. Rename Component
**From:** `gemini_api` → **To:** `ai_client_api`
- **Rationale:** Interface should be provider-agnostic (supports Gemini, OpenAI, Claude, etc.)
- Update workspace in root `pyproject.toml`
- Update all imports in other modules

### 2. Update `ai_client_api` Interface
**File:** `src/ai_client_api/src/ai_client_api/client.py`
- Add factory function `get_client()` that raises `NotImplementedError`
- Pattern: Same as `mail_client_api.get_client()`

**File:** `src/ai_client_api/src/ai_client_api/message.py`
- Add factory function `get_message()` that raises `NotImplementedError`
- Pattern: Same as `mail_client_api.get_message()`

**File:** `src/ai_client_api/src/ai_client_api/__init__.py`
- Export: `AIClient`, `Message`, `get_client`, `get_message`
- Remove `__all__` (not needed per TA feedback)

### 3. Update `gemini_impl` Implementation
**File:** `src/gemini_impl/src/gemini_impl/client.py`
- Keep existing `GeminiClient` class
- Add `get_client_impl()` factory function:
  ```python
  def get_client_impl(user_id: str, api_key: str, db_path: str = "conversations.db") -> ai_client_api.AIClient:
      return GeminiClient(api_key=api_key, db_path=db_path)
  ```
- Add `register()` function:
  ```python
  def register() -> None:
      ai_client_api.get_client = get_client_impl
  ```

**File:** `src/gemini_impl/src/gemini_impl/message.py`
- Keep existing `MessageImpl` class
- Add `get_message_impl()` factory function:
  ```python
  def get_message_impl(role: str, content: str) -> ai_client_api.Message:
      return MessageImpl(role=role, content=content)
  ```
- Add `register()` function:
  ```python
  def register() -> None:
      ai_client_api.get_message = get_message_impl
  ```

**File:** `src/gemini_impl/src/gemini_impl/__init__.py`
- Export: `GeminiClient`, `MessageImpl`, `get_client_impl`, `get_message_impl`, `OAuthManager`
- Create wrapper `register()` function that calls both client and message register functions
- Call `register()` at module import time (bottom of file)
- Remove `__all__` (not needed)

### 4. Update `gemini_service` Service
**File:** `src/gemini_service/src/gemini_service/api.py`
- Change imports: `from gemini_api.client import AIClient` → `from ai_client_api.client import AIClient`
- Update `_create_user_client()` to use registered factory:
  ```python
  def _create_user_client(user_id: str, api_key: str) -> AIClient:
      return ai_client_api.get_client(user_id=user_id, api_key=api_key, db_path=db_path)
  ```
- Keep environment variable approach for client type selection via `AI_CLIENT_TYPE`

### 5. Update `gemini_adapter` Adapter
**File:** `src/gemini_adapter/src/gemini_adapter/_impl.py`
- Change imports: `from gemini_api.client import AIClient` → `from ai_client_api.client import AIClient`

### 6. Update Root Configuration
**File:** `pyproject.toml`
- Update workspace members: `gemini_api` → `ai_client_api`
- Update mypy path to include `ai_client_api`

### 7. Update Documentation
- Update `mkdocs.yml` to use `ai_client_api` instead of `gemini_api`
- Update `docs/hw2-gemini.md` to explain the DI pattern
- Update `docs/api/gemini_api.md` → `docs/api/ai_client_api.md`

## Implementation Order
1. Rename `gemini_api` → `ai_client_api`
2. Add factory functions to `ai_client_api`
3. Update `ai_client_api/__init__.py`
4. Implement register pattern in `gemini_impl`
5. Update service and adapter imports
6. Update configuration files
7. Update documentation

## Why This Matters
- **Provider-agnostic:** Can swap Gemini for OpenAI/Claude/etc. with single import change
- **Proper DI:** Dependencies are injected at import time, not created in endpoints
- **Consistency:** Follows established pattern from mail_client_api
- **Extensibility:** Other modules import `gemini_impl` to automatically get registered implementation

## Example Usage After Refactoring
```python
import ai_client_api
import gemini_impl  # This registers GeminiClient as the implementation

# Now ai_client_api.get_client() returns GeminiClient instances
client = ai_client_api.get_client(user_id="user123", api_key="key", db_path="db")
```

If switching to OpenAI:
```python
import ai_client_api
import openai_impl  # This registers OpenAIClient as the implementation

# Now ai_client_api.get_client() returns OpenAIClient instances
client = ai_client_api.get_client(user_id="user123", api_key="key", db_path="db")
```
