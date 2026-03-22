"""Steam authentication helpers."""
from urllib.parse import urlencode, urlparse

import httpx
from fastapi import Request

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"


def build_steam_login_url(callback_url: str) -> str:
    """Build Steam OpenID login URL.

    callback_url example:
    http://localhost:8080/auth/steam/callback
    """
    parsed = urlparse(callback_url)
    realm = f"{parsed.scheme}://{parsed.netloc}"

    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": callback_url,
        "openid.realm": realm,
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
    }

    return f"{STEAM_OPENID_URL}?{urlencode(params)}"


def validate_steam_callback(request: Request) -> str | None:
    """Validate the Steam callback and return steam_id if valid."""
    params = dict(request.query_params)
    if not params:
        return None

    verify_data = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "check_authentication",
    }

    for key, value in params.items():
        if key.startswith("openid.") and key != "openid.mode":
            verify_data[key] = value

    try:
        res = httpx.post(STEAM_OPENID_URL, data=verify_data, timeout=10)
        res.raise_for_status()

        if "is_valid:true" not in res.text:
            return None
    except httpx.HTTPError:
        return None

    claimed_id = params.get("openid.claimed_id") or params.get("openid.identity")
    if not claimed_id:
        return None

    steam_id = claimed_id.rstrip("/").split("/")[-1]
    return steam_id