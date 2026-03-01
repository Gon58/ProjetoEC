import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app 

class TestAPIHealth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('main.check_postgres', return_value={"status": "up"})
    @patch('main.check_mongodb', return_value={"status": "up"})
    @patch('main.check_chromadb', return_value={"status": "up"})
    def test_health_healthy_status(self, mock_chromadb, mock_mongodb, mock_postgres):
        """Tests if the endpoint returns 200 OK when all dependencies are healthy."""
        response = self.client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    @patch('main.check_postgres', return_value={"status": "up"})
    @patch('main.check_mongodb', return_value={"status": "down"}) # Simulates failure
    @patch('main.check_chromadb', return_value={"status": "up"})
    def test_health_degraded_status(self, mock_chromadb, mock_mongodb, mock_postgres):
        """Tests if the endpoint returns 503 Service Unavailable when a dependency fails."""
        response = self.client.get("/health")
        
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "degraded")