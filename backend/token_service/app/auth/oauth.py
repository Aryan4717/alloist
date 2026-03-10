"""OAuth helpers for Google and GitHub."""

import secrets
from urllib.parse import urlencode

import httpx

from app.config import get_settings


def build_google_auth_url(state: str) -> str:
    """Build Google OAuth authorization URL."""
    settings = get_settings()
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def build_github_auth_url(state: str) -> str:
    """Build GitHub OAuth authorization URL."""
    settings = get_settings()
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "user:email read:user",
        "state": state,
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"


async def exchange_google_code(code: str) -> dict:
    """Exchange Google auth code for tokens and fetch user info."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()
        access_token = tokens["access_token"]

        # Get user info
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_resp.raise_for_status()
        return user_resp.json()


async def exchange_github_code(code: str) -> dict:
    """Exchange GitHub auth code for tokens and fetch user info."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens (GitHub requires application/x-www-form-urlencoded)
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "code": code,
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            raise ValueError("No access_token in GitHub response")

        # Get user info
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_resp.raise_for_status()
        user_data = user_resp.json()

        # GitHub may not include email in user endpoint; fetch from emails API
        email = user_data.get("email")
        if not email:
            emails_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if emails_resp.status_code == 200:
                emails = emails_resp.json()
                primary = next((e for e in emails if e.get("primary")), emails[0] if emails else None)
                if primary:
                    email = primary.get("email", "")

        return {
            "id": str(user_data["id"]),
            "email": email or f"{user_data['login']}@users.noreply.github.com",
            "name": user_data.get("name") or user_data.get("login", ""),
        }


def generate_state() -> str:
    """Generate CSRF state for OAuth."""
    return secrets.token_urlsafe(32)
