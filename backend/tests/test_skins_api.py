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