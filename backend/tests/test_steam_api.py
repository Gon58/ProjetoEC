import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app


class TestSteamAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.fake_steam_id = "76561198054759574"

    @patch("src.api.steam_routes.build_steam_login_url")
    def test_steam_login_redirects_to_steam(self, mock_build_login_url):
        mock_build_login_url.return_value = "https://steamcommunity.com/openid/login?mock=1"

        response = self.client.get("/auth/steam/login", follow_redirects=False)

        self.assertEqual(response.status_code, 307)
        self.assertEqual(
            response.headers["location"],
            "https://steamcommunity.com/openid/login?mock=1",
        )
        mock_build_login_url.assert_called_once()

    @patch("src.api.steam_routes.validate_steam_callback")
    def test_steam_callback_valid_sets_session_and_redirects(self, mock_validate_callback):
        mock_validate_callback.return_value = self.fake_steam_id

        response = self.client.get("/auth/steam/callback", follow_redirects=False)

        self.assertEqual(response.status_code, 307)
        self.assertEqual(
            response.headers["location"],
            "http://localhost:5173?steam_login=success",
        )

        me_response = self.client.get("/auth/me")
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(
            me_response.json(),
            {"steam_id": self.fake_steam_id},
        )

    @patch("src.api.steam_routes.validate_steam_callback")
    def test_steam_callback_invalid_returns_401(self, mock_validate_callback):
        mock_validate_callback.return_value = None

        response = self.client.get("/auth/steam/callback", follow_redirects=False)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Steam login failed")

    def test_steam_me_without_session_returns_null(self):
        response = self.client.get("/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"steam_id": None})

    @patch("src.api.steam_routes.validate_steam_callback")
    def test_steam_me_with_session_returns_steam_id(self, mock_validate_callback):
        mock_validate_callback.return_value = self.fake_steam_id

        self.client.get("/auth/steam/callback", follow_redirects=False)
        response = self.client.get("/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"steam_id": self.fake_steam_id})

    @patch("src.api.steam_routes.validate_steam_callback")
    def test_logout_clears_session(self, mock_validate_callback):
        mock_validate_callback.return_value = self.fake_steam_id

        self.client.get("/auth/steam/callback", follow_redirects=False)

        me_before = self.client.get("/auth/me")
        self.assertEqual(me_before.json(), {"steam_id": self.fake_steam_id})

        logout_response = self.client.post("/auth/logout")
        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(logout_response.json()["status"], "success")

        me_after = self.client.get("/auth/me")
        self.assertEqual(me_after.status_code, 200)
        self.assertEqual(me_after.json(), {"steam_id": None})

    def test_steam_profile_without_session_returns_401(self):
        response = self.client.get("/auth/steam/profile")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Not logged in")

    @patch("src.api.steam_routes.get_steam_profile")
    @patch("src.api.steam_routes.validate_steam_callback")
    def test_steam_profile_with_session_returns_profile(
        self,
        mock_validate_callback,
        mock_get_steam_profile,
    ):
        mock_validate_callback.return_value = self.fake_steam_id
        mock_get_steam_profile.return_value = {
            "status": "success",
            "player": {
                "steam_id": self.fake_steam_id,
                "persona_name": "PIRES",
                "profile_url": "https://steamcommunity.com/id/test/",
                "avatar": "https://example.com/avatar.jpg",
                "avatar_full": "https://example.com/avatar_full.jpg",
                "real_name": "Fernando",
                "country_code": "PT",
                "state_code": None,
                "city_id": None,
            },
        }

        self.client.get("/auth/steam/callback", follow_redirects=False)
        response = self.client.get("/auth/steam/profile")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(
            response.json()["player"]["steam_id"],
            self.fake_steam_id,
        )
        mock_get_steam_profile.assert_called_once_with(self.fake_steam_id)

    @patch("src.api.steam_routes.get_steam_profile")
    @patch("src.api.steam_routes.validate_steam_callback")
    def test_steam_profile_helper_failure_returns_502(
        self,
        mock_validate_callback,
        mock_get_steam_profile,
    ):
        mock_validate_callback.return_value = self.fake_steam_id
        mock_get_steam_profile.side_effect = Exception("Steam profile fetch failed")

        self.client.get("/auth/steam/callback", follow_redirects=False)
        response = self.client.get("/auth/steam/profile")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "Steam profile fetch failed")

    def test_steam_inventory_without_session_returns_401(self):
        response = self.client.get("/auth/steam/inventory")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Not logged in")

    @patch("src.api.steam_routes.get_steam_inventory")
    @patch("src.api.steam_routes.validate_steam_callback")
    def test_steam_inventory_with_session_returns_inventory(
        self,
        mock_validate_callback,
        mock_get_steam_inventory,
    ):
        mock_validate_callback.return_value = self.fake_steam_id
        mock_get_steam_inventory.return_value = {
            "status": "success",
            "inventory": {
                "steam_id": self.fake_steam_id,
                "items": [
                    {
                        "assetid": "1",
                        "classid": "100",
                        "instanceid": "200",
                        "amount": "1",
                        "name": "AK-47 | Redline",
                        "market_hash_name": "AK-47 | Redline (Field-Tested)",
                        "type": "Classified Rifle",
                        "icon_url": "mock_icon",
                        "icon_url_large": None,
                        "tradable": 1,
                        "marketable": 1,
                        "tags": [],
                    }
                ],
                "total_items": 1,
            },
        }

        self.client.get("/auth/steam/callback", follow_redirects=False)
        response = self.client.get("/auth/steam/inventory")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(response.json()["inventory"]["steam_id"], self.fake_steam_id)
        self.assertEqual(response.json()["inventory"]["total_items"], 1)
        mock_get_steam_inventory.assert_called_once_with(self.fake_steam_id)

    @patch("src.api.steam_routes.get_steam_inventory")
    @patch("src.api.steam_routes.validate_steam_callback")
    def test_steam_inventory_helper_failure_returns_502(
        self,
        mock_validate_callback,
        mock_get_steam_inventory,
    ):
        mock_validate_callback.return_value = self.fake_steam_id
        mock_get_steam_inventory.side_effect = Exception("Steam inventory fetch failed")

        self.client.get("/auth/steam/callback", follow_redirects=False)
        response = self.client.get("/auth/steam/inventory")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "Steam inventory fetch failed")


if __name__ == "__main__":
    unittest.main()