"""Steam authentication and game endpoints."""
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse

from ..schemas.steam import SteamMeResponse
from ..services.steam_api import get_steam_inventory, get_steam_profile
from ..services.steam_auth import build_steam_login_url, validate_steam_callback

steam_router = APIRouter(prefix="/auth")


@steam_router.get("/steam/login")
def steam_login(request: Request) -> RedirectResponse:
    """Redirect to Steam for user login via OpenID."""
    callback_url = str(request.url_for("steam_callback"))
    redirect_url = build_steam_login_url(callback_url)
    return RedirectResponse(url=redirect_url)


@steam_router.get("/steam/callback", name="steam_callback")
def steam_callback(request: Request) -> RedirectResponse:
    """Handle Steam callback and store steam_id in session."""
    steam_id = validate_steam_callback(request)
    if not steam_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Steam login failed",
        )

    request.session["steam_id"] = steam_id
    return RedirectResponse(url="http://localhost:5173?steam_login=success")


@steam_router.post("/logout")
def steam_logout(request: Request) -> JSONResponse:
    """Logout user by clearing steam_id from session."""
    request.session.pop("steam_id", None)
    return JSONResponse({"status": "success", "message": "Logged out"})


@steam_router.get("/me")
def steam_me(request: Request) -> SteamMeResponse:
    """Return current logged-in Steam user ID."""
    steam_id = request.session.get("steam_id")
    return SteamMeResponse(steam_id=steam_id)


@steam_router.get("/steam/profile")
def steam_profile(request: Request) -> JSONResponse:
    """Return Steam profile for logged-in user."""
    steam_id = request.session.get("steam_id")
    if not steam_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in",
        )

    try:
        result = get_steam_profile(steam_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@steam_router.get("/steam/inventory")
def steam_inventory(request: Request) -> JSONResponse:
    """Return Steam CS2 inventory for logged-in user."""
    steam_id = request.session.get("steam_id")
    if not steam_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in",
        )

    try:
        result = get_steam_inventory(steam_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )