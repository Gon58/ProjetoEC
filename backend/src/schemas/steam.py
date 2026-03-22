"""Pydantic models for Steam endpoints."""
from pydantic import BaseModel


class SteamLoginResponse(BaseModel):
    redirect_url: str


class SteamMeResponse(BaseModel):
    steam_id: str | None


class SteamProfileResponse(BaseModel):
    status: str
    player: dict | None


class SteamInventoryResponse(BaseModel):
    status: str
    inventory: dict | None
