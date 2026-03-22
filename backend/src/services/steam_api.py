"""Steam API helpers."""
from typing import Any, Dict

import httpx

from ..core.config import STEAM_API_KEY

STEAM_PROFILE_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
STEAM_INVENTORY_URL_TEMPLATE = "https://steamcommunity.com/inventory/{steam_id}/730/2"


def get_steam_profile(steam_id: str) -> Dict[str, Any]:
    if not STEAM_API_KEY:
        raise ValueError("STEAM_API_KEY is not configured")

    params = {
        "key": STEAM_API_KEY,
        "steamids": steam_id,
    }

    res = httpx.get(STEAM_PROFILE_URL, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()

    players = data.get("response", {}).get("players", [])
    if not players:
        return {"status": "error", "message": "Player not found"}

    p = players[0]
    return {
        "status": "success",
        "player": {
            "steam_id": p.get("steamid"),
            "persona_name": p.get("personaname"),
            "profile_url": p.get("profileurl"),
            "avatar": p.get("avatar"),
            "avatar_full": p.get("avatarfull"),
            "real_name": p.get("realname"),
            "country_code": p.get("loccountrycode"),
            "state_code": p.get("locstatecode"),
            "city_id": p.get("loccityid"),
        },
    }


def get_steam_inventory(steam_id: str) -> Dict[str, Any]:
    inventory_url = STEAM_INVENTORY_URL_TEMPLATE.format(steam_id=steam_id)
    params = {
        "l": "english",
        "count": 2000,
    }

    res = httpx.get(
        inventory_url,
        params=params,
        timeout=20,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    res.raise_for_status()
    data = res.json()

    assets = data.get("assets", [])
    descriptions = data.get("descriptions", [])

    descriptions_map = {
        f"{desc.get('classid')}_{desc.get('instanceid', '0')}": desc
        for desc in descriptions
    }

    items = []
    for asset in assets:
        key = f"{asset.get('classid')}_{asset.get('instanceid', '0')}"
        desc = descriptions_map.get(key, {})

        items.append(
            {
                "assetid": asset.get("assetid"),
                "classid": asset.get("classid"),
                "instanceid": asset.get("instanceid"),
                "amount": asset.get("amount"),
                "name": desc.get("name"),
                "market_hash_name": desc.get("market_hash_name"),
                "type": desc.get("type"),
                "icon_url": desc.get("icon_url"),
                "icon_url_large": desc.get("icon_url_large"),
                "tradable": desc.get("tradable"),
                "marketable": desc.get("marketable"),
                "tags": desc.get("tags", []),
            }
        )

    return {
        "status": "success",
        "inventory": {
            "steam_id": steam_id,
            "items": items,
            "total_items": len(items),
        },
    }