"""OAuth authentication routes for Jira integration."""

import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from ticket_impl.config import settings
from ticket_impl.oauth import (
    build_authorize_url,
    exchange_code_for_tokens,
    extract_cloud_id_from_token,
    fetch_cloud_id_from_api,
)
from ticket_impl.storage import get_tokens, is_expired

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/login")
async def oauth_login(user_id: str = Query(..., description="User identifier (e.g., email)")) -> RedirectResponse:
    """Initiate OAuth flow for Jira."""
    try:
        auth_url = build_authorize_url(state=user_id)
        logger.info(f"Redirecting user {user_id} to Jira OAuth")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Error building auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from Jira"),
    state: str = Query(..., description="User ID passed in state"),
) -> HTMLResponse:
    """Handle OAuth callback from Jira."""
    try:
        user_id = state
        logger.info(f"Processing OAuth callback for user {user_id}")

        access_token, refresh_token, expires_in = await exchange_code_for_tokens(user_id, code)

        cloud_id = extract_cloud_id_from_token(access_token)

        if not cloud_id:
            cloud_id = await fetch_cloud_id_from_api(access_token)

        if cloud_id:
            logger.info(f"Successfully authenticated user {user_id}, cloud_id: {cloud_id}")
            if settings.jira_cloud_id == "placeholder-will-get-from-oauth":
                settings.jira_cloud_id = cloud_id
                logger.info(f"Updated JIRA_CLOUD_ID to {cloud_id}")
        else:
            logger.warning("Could not extract cloud_id from token or API")

        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; text-align: center;">
                    <h1 style="color: #0052CC;">✓ Authentication Successful!</h1>
                    <p>You have successfully authenticated with Jira.</p>
                    <p><strong>User:</strong> {user_id}</p>
                    <p><strong>Cloud ID:</strong> {cloud_id or "Not detected (check logs)"}</p>
                    <p style="margin-top: 30px; color: #666;">You can close this window and return to your application.</p>
                    {f'<p style="margin-top: 20px; padding: 10px; background: #E3FCEF; border-radius: 5px;"><strong>Note:</strong> Add this to your .env file:<br/><code>JIRA_CLOUD_ID={cloud_id}</code></p>' if cloud_id else ""}
                </body>
            </html>
            """,
            status_code=200,
        )

    except Exception as e:
        logger.exception(f"OAuth callback error: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Authentication Failed</title></head>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; text-align: center;">
                    <h1 style="color: #DE350B;">✗ Authentication Failed</h1>
                    <p>There was an error during authentication:</p>
                    <p style="color: #666;"><code>{str(e)}</code></p>
                    <p style="margin-top: 30px;">
                        <a href="/api/v1/auth/login?user_id={state}" style="color: #0052CC;">Try Again</a>
                    </p>
                </body>
            </html>
            """,
            status_code=500,
        )


@router.get("/status")
async def auth_status(user_id: str = Query(..., description="User identifier")) -> dict[str, str | bool | None]:
    """Check if user has valid OAuth tokens."""
    try:
        tokens = get_tokens(user_id)

        if not tokens:
            return {
                "authenticated": False,
                "user_id": user_id,
                "message": "No tokens found. Please authenticate.",
                "login_url": f"/api/v1/auth/login?user_id={user_id}",
            }

        expired = is_expired(tokens)

        return {
            "authenticated": not expired,
            "user_id": user_id,
            "expires_at": tokens.expires_at.isoformat() if tokens.expires_at else None,
            "expired": expired,
            "message": "Token expired. Please re-authenticate." if expired else "Authenticated",
            "login_url": f"/api/v1/auth/login?user_id={user_id}" if expired else None,
        }

    except Exception as e:
        logger.exception(f"Error checking auth status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
