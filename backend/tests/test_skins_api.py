import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app


class TestSkinsAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("src.api.routes.fetch_skinport_skins")
    def test_get_skins_success(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": "AK-47 | Redline", "price": 10.5},
            {"name": "AWP | Asiimov", "price": 55.0},
        ]

        response = self.client.get("/skins?limit=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        mock_fetch.assert_called_once_with(limit=2)

    @patch("src.api.routes.fetch_skinport_skins")
    def test_get_skins_default_limit(self, mock_fetch):
        mock_fetch.return_value = []

        response = self.client.get("/skins")

        self.assertEqual(response.status_code, 200)
        mock_fetch.assert_called_once_with(limit=100)

    @patch("src.api.routes.fetch_skinport_skins")
    def test_get_skins_exception(self, mock_fetch):
        mock_fetch.side_effect = Exception("Database connection error")

        response = self.client.get("/skins")

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json())

    @patch("src.api.routes.fetch_skinport_skin_by_id")
    def test_get_skin_by_id_success(self, mock_fetch):
        mock_data = {"id": 1, "name": "AK-47 | Redline", "price": 10.5}
        mock_fetch.return_value = mock_data

        response = self.client.get("/skins/id/1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), mock_data)
        mock_fetch.assert_called_once_with(skin_id=1)

    @patch("src.api.routes.fetch_skinport_skin_by_id")
    def test_get_skin_by_id_not_found(self, mock_fetch):
        mock_fetch.return_value = None

        response = self.client.get("/skins/id/999")

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Skin not found")

    @patch("src.api.routes.fetch_skinport_skin_by_id")
    def test_get_skin_by_id_exception(self, mock_fetch):
        mock_fetch.side_effect = Exception("Database error")

        response = self.client.get("/skins/id/1")

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json())

    @patch("src.api.routes.fetch_most_expensive_skinport_skins")
    def test_get_most_expensive_skins_success(self, mock_fetch):
        mock_data = [
            {"name": "Dragon Lore", "price": 1000.0},
            {"name": "Souvenir AWP Dragon Lore", "price": 5000.0},
        ]
        mock_fetch.return_value = mock_data

        response = self.client.get("/skins/most-expensive?limit=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        mock_fetch.assert_called_once_with(limit=2)

    @patch("src.api.routes.fetch_most_expensive_skinport_skins")
    def test_get_most_expensive_skins_default_limit(self, mock_fetch):
        mock_fetch.return_value = []

        response = self.client.get("/skins/most-expensive")

        self.assertEqual(response.status_code, 200)
        mock_fetch.assert_called_once_with(limit=10)

    @patch("src.api.routes.fetch_most_expensive_skinport_skins")
    def test_get_most_expensive_skins_exception(self, mock_fetch):
        mock_fetch.side_effect = Exception("Database error")

        response = self.client.get("/skins/most-expensive")

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json())

    @patch("src.api.routes.fetch_best_selling_skinport_skins")
    def test_get_best_selling_skins_success(self, mock_fetch):
        mock_data = [
            {"name": "AK-47 | Redline", "price": 10.5, "sales": 1000},
            {"name": "M4A4 | Howl", "price": 100.0, "sales": 800},
        ]
        mock_fetch.return_value = mock_data

        response = self.client.get("/skins/best-selling?limit=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        mock_fetch.assert_called_once_with(limit=2)

    @patch("src.api.routes.fetch_best_selling_skinport_skins")
    def test_get_best_selling_skins_default_limit(self, mock_fetch):
        mock_fetch.return_value = []

        response = self.client.get("/skins/best-selling")

        self.assertEqual(response.status_code, 200)
        mock_fetch.assert_called_once_with(limit=10)

    @patch("src.api.routes.fetch_best_selling_skinport_skins")
    def test_get_best_selling_skins_exception(self, mock_fetch):
        mock_fetch.side_effect = Exception("Database error")

        response = self.client.get("/skins/best-selling")

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json())