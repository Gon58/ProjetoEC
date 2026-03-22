import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app


class TestLogsAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("src.services.logs.fetch_parent_ingestion_logs")
    def test_get_parent_logs_default(self, mock_fetch_parents):
        mock_fetch_parents.return_value = (
            [
                {
                    "id": 1,
                    "timestamp": "2026-03-16 10:12:05",
                    "source": "postgres_loader",
                    "database": "postgres",
                    "description": "Parent log",
                    "children_count": 2,
                }
            ],
            1,
        )

        response = self.client.get("/logs")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["level"], "parent")
        self.assertIn("items", payload)
        self.assertGreater(len(payload["items"]), 0)
        self.assertIn("pagination", payload)
        self.assertTrue(payload["items"][0]["has_children"])

    @patch("src.services.logs.fetch_ingestion_log_by_id")
    @patch("src.services.logs.fetch_child_ingestion_logs")
    def test_get_child_logs_for_parent(self, mock_fetch_children, mock_fetch_parent):
        mock_fetch_children.return_value = (
            [
                {
                    "id": 101,
                    "parent_log_id": 1,
                    "timestamp": "2026-03-16 10:12:25",
                    "source": "postgres_loader",
                    "database": "postgres",
                    "step": "record_loaded",
                    "description": "Child log",
                }
            ],
            1,
        )
        mock_fetch_parent.return_value = {
            "id": 1,
            "timestamp": "2026-03-16 10:12:05",
            "source": "postgres_loader",
            "database": "postgres",
            "description": "Parent log",
            "status": "success",
        }

        response = self.client.get("/logs", params={"parent_id": 1, "page": 1, "page_size": 2})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["level"], "child")
        self.assertEqual(payload["parent_id"], 1)
        self.assertLessEqual(len(payload["items"]), 2)
        self.assertEqual(payload["items"][0]["step"], "record_loaded")

    @patch("src.services.logs.fetch_parent_ingestion_logs")
    def test_logs_pagination_fields(self, mock_fetch_parents):
        mock_fetch_parents.return_value = ([], 0)

        response = self.client.get("/logs", params={"page": 1, "page_size": 2})

        self.assertEqual(response.status_code, 200)
        pagination = response.json()["pagination"]
        self.assertEqual(pagination["page_size"], 2)
        self.assertEqual(pagination["page"], 1)
        self.assertIn("total_pages", pagination)
        self.assertIn("has_next", pagination)
