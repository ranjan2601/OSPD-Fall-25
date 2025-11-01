# Python Application Template: Component-Based Microservices

[![CircleCI](https://dl.circleci.com/status-badge/img/circleci/QJXxW5Kg3MhaRTXDr47FTf/bcb4e941-0b5f-479a-889b-9b98e69919c2/tree/dev.svg?style=shield)](https://dl.circleci.com/status-badge/redirect/circleci/QJXxW5Kg3MhaRTXDr47FTf/bcb4e941-0b5f-479a-889b-9b98e69919c2/tree/dev)
[![Coverage](https://img.shields.io/badge/coverage-91%2B%25-brightgreen)](https://app.circleci.com/pipelines/circleci/QJXxW5Kg3MhaRTXDr47FTf/bcb4e941-0b5f-479a-889b-9b98e69919c2)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Live Demo](https://img.shields.io/badge/demo-live-success)](https://ospd-mail-client-hw1.fly.dev/docs)

This repository serves as a professional-grade template for modern Python microservices. It demonstrates robust, component-based architecture by implementing:

1. **Mail Client System** - AI-powered email assistant with Gmail API integration
2. **Gemini AI Service** - FastAPI service providing AI chat capabilities with Google Gemini

The project emphasizes strict separation of concerns, dependency injection, OAuth 2.0 authentication, and a comprehensive automated toolchain to enforce code quality and best practices.

## Quick Start

### Setup
```bash
# Install dependencies
uv sync --all-packages --extra dev

# Activate virtual environment
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### Run the FastAPI Server

**Option 1: Use the Live Demo** 
The service is deployed and running on fly.io:
- **API Documentation (Swagger UI)**: https://ospd-mail-client-hw1.fly.dev/docs
- **Alternative Docs (ReDoc)**: https://ospd-mail-client-hw1.fly.dev/redoc
- **API Endpoint**: https://ospd-mail-client-hw1.fly.dev/messages

> Note: The deployed app uses a mock client with 3 test messages for demonstration purposes.

**Option 2: Run locally**
```bash
uv run uvicorn mail_client_service.main:app --reload
```

**Option 3: Run with Docker**
```bash
# Build the Docker image
docker build -t mail-client-service .

# Run the container
docker run -d -p 8000:8000 --name mail-service mail-client-service

# Test the service
curl http://localhost:8000/
curl http://localhost:8000/messages

# Stop the container
docker stop mail-service && docker rm mail-service
```

### Run Tests
```bash
# Type checking
uv run mypy src tests

# Unit tests only
uv run pytest src/

# All tests except those requiring local credentials (CI-compatible)
uv run pytest src/ tests/ -m "not local_credentials"
```

### Required Credentials Setup

#### 1. Google Gemini API Key
To use the Gemini AI chat service:

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Set the environment variable or create a `.env` file:
   ```bash
   # Option 1: Set environment variable
   export GEMINI_API_KEY=your_api_key_here

   # Option 2: Create .env file in project root
   # Add this line to .env:
   GEMINI_API_KEY=your_api_key_here
   ```
4. **Note:** Without this key, the Gemini service uses a mock client for testing

#### 2. Gemini Database
The Gemini service automatically creates an SQLite database to store conversation history:
- **Location:** `conversations.db` (created automatically in project root)
- **Purpose:** Persists per-user chat history
- **Note:** This file is automatically ignored by `.gitignore` and should not be committed

### Gmail Authentication
To connect to your Gmail account:

1. Follow the [Google Cloud instructions](https://developers.google.com/gmail/api/quickstart/python#authorize_credentials_for_a_desktop_application) to enable the Gmail API and download OAuth 2.0 credentials
2. Rename the downloaded file to `credentials.json` and place it in the project root
3. Set `interactive=True` in `main.py` and run it
4. Follow the command-line instructions to log in and authorize the application

### Gemini AI Service

The Gemini AI Service provides a FastAPI-based chat interface with Google's Gemini AI model.

**Run the Service:**
```bash
# Start the FastAPI server
uv run uvicorn gemini_service.main:app --reload

# Access the API documentation
# Open browser: http://localhost:8000/docs
```

**Available Endpoints:**
- `POST /chat` - Send a message to AI and get response
- `GET /history/{user_id}` - Retrieve conversation history
- `DELETE /history/{user_id}` - Clear conversation history
- `GET /auth/login` - Get OAuth authorization URL
- `POST /auth/callback` - Handle OAuth callback
- `DELETE /auth/{user_id}` - Revoke OAuth credentials

**Authentication:**
Set the `GEMINI_API_KEY` environment variable or use OAuth 2.0 flow. Without credentials, the service uses a mock client for testing.

**Testing:**
```bash
# Run Gemini service tests
uv run pytest src/gemini_service/tests/ -v

# Test coverage (should be 85%+)
uv run pytest src/gemini_api src/gemini_impl src/gemini_service --cov
```

## Architectural Philosophy

This project is built on the principle of "programming integrated over time." The architecture is designed to combat complexity and ensure the system is maintainable and evolvable.

-   **Component-Based Design:** The system is broken down into four distinct, self-contained components. Each component has a single responsibility and can be "forklifted" out of this project to be used in another with minimal effort.
-   **Interface-Implementation Separation:** Every piece of functionality is defined by an abstract **contract** implemented as an ABC (the "what") and fulfilled by a concrete **implementation** (the "how"). This decouples our business logic from specific technologies (like Gmail).
-   **Dependency Injection:** Implementations are "injected" into the abstract contracts at runtime. This means consumers of the API only ever depend on the stable interface, not the volatile implementation details.

## Core Components

The project is a `uv` workspace containing multiple service implementations:

### Mail Client System (HW1)
1.  **`mail_client_api`**: Defines the abstract `Client` base class (ABC). This is the contract for what actions a mail client can perform (e.g., `get_messages`).
2.  **`gmail_client_impl`**: Provides the `GmailClient` class, a concrete implementation that uses the Google API to perform the actions defined in the `Client` abstraction.
3.  **`mail_client_service`**: FastAPI server providing HTTP REST API for mail client operations with dependency injection.
4.  **`mail_client_service_client`**: Auto-generated HTTP client using `openapi-python-client` for programmatic API access.
5.  **`mail_client_adapter`**: Adapter implementing `mail_client_api.Client` that calls the HTTP service (drop-in replacement for `gmail_client_impl`).

### Gemini AI Service (HW2)
6.  **`gemini_api`**: Defines the abstract `AIClient` base class (ABC). Contract for AI chat service operations (send messages, get history, clear conversations).
7.  **`gemini_impl`**: Concrete implementation using Google Gemini API with OAuth 2.0 authentication and SQLite-based conversation storage.
8.  **`gemini_service`**: FastAPI server exposing AI chat endpoints with OAuth 2.0 flow (login, callback, revoke) and comprehensive error handling.
9.  **`gemini_service_api_client`**: Auto-generated HTTP client using `openapi-python-client` for programmatic API access to the Gemini service.
10. **`gemini_adapter`**: Adapter implementing `gemini_api.AIClient` that calls the HTTP service (drop-in replacement for `gemini_impl`).

## Project Structure

```
ta-assignment/
├── src/                          # Source packages (uv workspace members)
│   ├── mail_client_api/          # [HW1] Abstract mail client base class (ABC)
│   ├── gmail_client_impl/        # [HW1] Gmail-specific client implementation
│   ├── mail_client_service/      # [HW1] FastAPI HTTP REST API server
│   ├── mail_client_service_client/ # [HW1] Auto-generated HTTP client
│   ├── mail_client_adapter/      # [HW1] Adapter for HTTP service client
│   ├── gemini_api/               # [HW2] Abstract AI client base class (ABC)
│   ├── gemini_impl/              # [HW2] Gemini API implementation with OAuth 2.0
│   ├── gemini_service/           # [HW2] FastAPI AI chat service
│   ├── gemini_service_api_client/ # [HW2] Auto-generated HTTP client
│   └── gemini_adapter/           # [HW2] Adapter for HTTP service client
├── tests/                        # Integration and E2E tests
│   ├── integration/              # Component integration tests
│   └── e2e/                      # End-to-end application tests
├── docs/                         # Documentation source files
├── .circleci/                    # CircleCI configuration
├── main.py                       # Main application entry point
├── pyproject.toml               # Project configuration (dependencies, tools)
├── uv.lock                      # Locked dependency versions
└── credentials.json             # Google OAuth credentials (local only)
```

## Project Setup

### 1. Prerequisites

-   Python 3.11 or higher
-   `uv` – A fast, all-in-one Python package manager.

### 2. Initial Setup

1.  **Install `uv`:**
    ```bash
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    ```

2.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd ta-assignment
    ```

3.  **Set Up Google Credentials:**
    -   Follow the [Google Cloud instructions](https://developers.google.com/gmail/api/quickstart/python#authorize_credentials_for_a_desktop_application) to enable the Gmail API and download your OAuth 2.0 credentials.
    -   Rename the downloaded file to `credentials.json` and place it in the root of this project.
    -   **Alternative**: For CI/CD environments, you can use environment variables instead:
        ```bash
        export GMAIL_CLIENT_ID="your_client_id"
        export GMAIL_CLIENT_SECRET="your_client_secret"
        export GMAIL_REFRESH_TOKEN="your_refresh_token"
        ```
    -   **Important:** Credential files contain secrets and are ignored by `.gitignore`.

4.  **Create and Sync the Virtual Environment:**
    This single command creates a `.venv` folder and installs all packages (including workspace members and development tools) defined in `uv.lock`.
    ```bash
    uv sync --all-packages --extra dev
    ```

5.  **Activate the Virtual Environment:**
    ```bash
    # macOS / Linux
    source .venv/bin/activate
    # Windows (PowerShell)
    .venv\Scripts\Activate.ps1
    ```

6.  **Perform Initial Authentication:**
    Run the main application once to perform the interactive OAuth flow. This will open a browser window for you to grant permission.
    ```bash
    uv run python main.py
    ```
    After you approve, a `token.json` file will be created. This file is also ignored by `.gitignore` and will be used for authentication in subsequent runs.

## Development Workflow

All commands should be run from the project root with the virtual environment activated.

### Running the Application

To run the main demonstration script:
```bash
uv run python main.py
```

### Running the Toolchain

-   **Linting & Formatting (Ruff):**
    The project uses Ruff with comprehensive rules configured in `pyproject.toml`.
    ```bash
    # Check for issues
    uv run ruff check .
    # Automatically fix issues
    uv run ruff check . --fix
    # Check formatting
    uv run ruff format --check .
    # Apply formatting
    uv run ruff format .
    ```

-   **Static Type Checking (MyPy):**
    ```bash
    uv run mypy src tests
    ```

-   **Testing (Pytest):**

    I'd recommend only running: `uv run pytest src/ tests/ -m "not local_credentials" -v` for simplicity.

    The project uses a comprehensive testing strategy with different test categories.
    ```bash
    # Run all tests (includes unit, integration, and e2e tests)
    uv run pytest

    # Run only unit tests (fast, no external dependencies - from src/ directories)
    uv run pytest src/

    # Run all tests except those requiring local credential files
    uv run pytest src/ tests/ -m "not local_credentials"

    # Run only integration tests (requires environment variables or credentials)
    uv run pytest -m integration

    # Run only end-to-end tests (requires credentials)
    uv run pytest -m e2e

    # Run only CircleCI-compatible tests (CI/CD environment)
    uv run pytest -m circleci

    # Run tests with coverage reporting
    uv run pytest --cov=src --cov-report=term-missing
    ```

### Viewing Documentation

This project uses MkDocs for documentation.
```bash
# Start the live-reloading documentation server
uv run mkdocs serve
```
Open your browser to `http://127.0.0.1:8000` to view the site.

## Testing Infrastructure

The project implements a sophisticated testing strategy designed for both local development and CI/CD environments:

### Test Categories

- **Unit Tests** (`src/*/tests/`): Fast, isolated tests with mocked dependencies
- **Integration Tests** (`tests/integration/`): Tests that verify component interactions
- **End-to-End Tests** (`tests/e2e/`): Full application workflow tests
- **CircleCI Tests**: CI/CD-compatible tests that handle missing credentials gracefully
- **Local Credentials Tests**: Tests that require `credentials.json` or `token.json` files

### Test Markers

The project uses pytest markers to categorize tests:
```bash
@pytest.mark.unit              # Fast unit tests
@pytest.mark.integration       # Integration tests
@pytest.mark.e2e              # End-to-end tests
@pytest.mark.circleci         # CI/CD compatible
@pytest.mark.local_credentials # Requires local auth files
```

### Authentication in Tests

The testing infrastructure handles different authentication scenarios:
- **Local Development**: Uses `credentials.json` and `token.json` files
- **CI/CD Environment**: Uses environment variables (`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`)
- **Missing Credentials**: Tests fail fast with clear error messages (no hanging)

## Continuous Integration

The project includes a comprehensive CircleCI configuration (`.circleci/config.yml`) with:

- **All Branches**: Unit tests, linting, and CI-compatible tests
- **Main/Develop**: Additional integration tests with real Gmail API calls
- **Artifacts**: Coverage reports, test results, and build summaries

See `docs/circleci-setup.md` for detailed CI/CD setup instructions.

## Development Workflow

### Quick Start
1. **Install dependencies**: `uv sync --all-packages --extra dev`
2. **Run tests**: `uv run pytest tests/ -v` or `uv run pytest src/ tests/ -m "not local_credentials" -v`
3. **Check code quality**: `uv run ruff check . && uv run ruff format --check .`
4. **Fix formatting**: `uv run ruff format .`
5. **View documentation**: `uv run mkdocs serve`

### Best Practices
- Run unit tests (`uv run pytest src/`) during development for fast feedback
- Use integration tests (`uv run pytest -m integration`) to verify component interactions
- Run full test suite (`uv run pytest`) before pushing to ensure CI compatibility
- The CircleCI pipeline provides automated validation on every push