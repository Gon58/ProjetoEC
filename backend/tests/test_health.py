import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app


class TestAPIHealth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("src.api.routes.check_postgres", return_value={"status": "up"})
    @patch("src.api.routes.check_mongodb", return_value={"status": "up"})
    @patch("src.api.routes.check_chromadb", return_value={"status": "up"})
    def test_health_healthy_status(self, mock_chromadb, mock_mongodb, mock_postgres):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    @patch("src.api.routes.check_postgres", return_value={"status": "up"})
    @patch("src.api.routes.check_mongodb", return_value={"status": "down"})
    @patch("src.api.routes.check_chromadb", return_value={"status": "up"})
    def test_health_degraded_status(self, mock_chromadb, mock_mongodb, mock_postgres):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "degraded")