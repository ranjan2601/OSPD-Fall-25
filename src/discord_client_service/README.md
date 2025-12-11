# Discord Client Service

RESTful FastAPI service that exposes Discord chat operations and manages OAuth2
credentials. This service has been simplified: credentials and OAuth state are
kept in-memory (server-side) as short-lived sessions; there is no database
initialized by this package.

## Key details (current system)

- OAuth2 flow and credential storage are in-memory and short-lived. See
	`src/discord_client_service/auth_session.py` for TTLs. (STATE_TTL=300s,
	SESSION_TTL=3600s)
- Endpoints use `guild_id` as the primary credential key (not per-user IDs).
- A HttpOnly cookie named `session_id` is used to authorize access to
	guild-scoped endpoints. The cookie is set during the OAuth callback.
- The application exposes an OpenAPI schema at `/openapi.json` and interactive
	docs at `/docs` when run with Uvicorn.

## Running the service

Start the FastAPI app with Uvicorn from the repository root:

```powershell
uvicorn discord_client_service.service:app --reload
```

By default the app will listen on `http://127.0.0.1:8000` (Uvicorn defaults).

## Environment variables

Required environment variables used by this service and the underlying
Discord implementation (`discord_client_impl`):

- `DISCORD_CLIENT_ID` – Discord application client ID
- `DISCORD_CLIENT_SECRET` – Discord application client secret
- `DISCORD_REDIRECT_URI` – OAuth2 redirect URI registered in your Discord app
- `DISCORD_BOT_TOKEN` – Application bot token (used for some guild-level
	operations such as listing channels or having the bot leave a guild). If
	not provided, some guild-level operations may require the bot to be
	installed into the guild.
- `DISCORD_PUBLIC_KEY` – Public key for discord app

Notes:
- The service does not use a local database for credentials; remove any
	reference to `DISCORD_DB_PATH` (it is not required).
- Make sure the `DISCORD_REDIRECT_URI` you register in the Discord
	developer console matches where the service is reachable, for example
	`http://localhost:8000/auth/callback` when running locally.

## OAuth & session behavior

- `GET /auth/login` returns an authorization URL you should redirect the user
	to. The server also creates a short-lived server-side state to protect the
	OAuth exchange.
- Discord will redirect back to `GET /auth/callback` with a `code` and
	`state`. The callback exchanges the code for tokens and stores credentials
	in-memory for the `guild_id` recovered from the state (or `guild_id` query
	param if provided). A `session_id` cookie is set on success (HttpOnly,
	SameSite=Lax).

## API Endpoints (summary)

Authentication

- `GET /auth/login` — Initialize OAuth2 flow. Returns an object with
	`authorization_url`.
- `GET /auth/callback` — OAuth2 callback (expects `code`, optional `state`
	and/or `guild_id`). Exchanges code for tokens and sets the `session_id`
	cookie.
- `GET /auth/status/{guild_id}` — Check whether credentials exist for a
	given guild (requires session cookie permitting access to that guild).
- `DELETE /auth/logout/{guild_id}` — Delete stored credentials for the
	guild and attempt to have the bot leave the guild (requires session).

Channels

- `GET /guilds/{guild_id}/channels` — List guild channels. Uses the
	application bot token when available.
- `GET /{guild_id}/channels/{channel_id}` — Get channel info (requires
	session cookie).

Messages

- `GET /{guild_id}/channels/{channel_id}/messages` — Get messages (query
	param `limit` available, default 10, max 100).
- `POST /{guild_id}/channels/{channel_id}/messages` — Send a message. JSON
	body: `{ "content": "..." }`.
- `DELETE /{guild_id}/channels/{channel_id}/messages/{message_id}` — Delete a
	message.

All guild-scoped endpoints use `require_guild_access` dependency which checks
the `session_id` cookie. If the session is missing, expired, or does not
include the requested `guild_id`, the endpoint returns HTTP 403.

## OpenAPI / docs

- Interactive docs: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json` (a committed
	`openapi.json` lives in the package root for client generation).

To regenerate the committed `openapi.json` after API changes run the
project-level script (from repository root):

```powershell
uv run python generate_discord_openapi.py
```

Note: generate_discord_openapi.py is located on root.

## Development

Run tests for the entire repository or the package tests from the root
directory. The project uses pytest (see pyproject.toml for test deps).

Run tests:

```powershell
uv run pytest
```

Type checking:

```powershell
uv run mypy src --explicit-package-bases
```

Linting:

```powershell
uv run ruff check .
```

## Notes and next steps

- This service uses an in-memory store for OAuth state, sessions, and
	credentials. For production, replace `auth_session` with a durable store
	(Redis, database) so sessions survive restarts and credentials are
	persisted.
- The `discord_client_impl` library used by this service still reads
	`DISCORD_REDIRECT_URI` and other env vars — ensure they are consistent
	with the service's public URL.
