"""
Tests for vector search and indexing using ChromaDB with Ollama embeddings.

Tests:
- Document indexing
- Embedding generation
- Semantic vector search
- API integration
"""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app


class TestVectorialIndexing(unittest.TestCase):
    """Tests for document indexing for vector search."""

    def setUp(self):
        """Sets up the API test client."""
        self.client = TestClient(app)

    @patch('src.api.routes.index_document')
    def test_index_document_success(self, mock_index):
        """Tests successful document indexing."""
        mock_index.return_value = {
            "status": "success",
            "doc_id": "test_doc",
            "chunks_indexed": 2,
        }

        payload = {
            "doc_id": "test_doc",
            "text": "This is a test document for indexing. " * 10,
            "metadata": {"source": "test"},
        }

        response = self.client.post("/index", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(response.json()["chunks_indexed"], 2)
        mock_index.assert_called_once()

    @patch('src.api.routes.index_document')
    def test_index_document_failure(self, mock_index):
        """Tests failure in document indexing."""
        mock_index.return_value = {
            "status": "error",
            "message": "ChromaDB connection failed",
        }

        payload = {
            "doc_id": "test_doc",
            "text": "Some text",
        }

        response = self.client.post("/index", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")


class TestVectorialSearch(unittest.TestCase):
    """Tests for semantic vector search."""

    def setUp(self):
        """Sets up the API test client."""
        self.client = TestClient(app)

    @patch('src.api.routes.search_documents')
    def test_search_documents_success(self, mock_search):
        """Tests successful document search."""
        mock_search.return_value = {
            "status": "success",
            "query": "machine learning",
            "total_results": 2,
            "results": [
                {
                    "chunk_id": "doc1_chunk_0",
                    "text": "Machine learning is powerful",
                    "distance": 0.15,
                    "metadata": {"doc_id": "doc1"},
                },
                {
                    "chunk_id": "doc2_chunk_1",
                    "text": "Learning from data",
                    "distance": 0.42,
                    "metadata": {"doc_id": "doc2"},
                },
            ],
        }

        payload = {
            "query": "machine learning",
            "n_results": 5,
        }

        response = self.client.post("/search", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_results"], 2)
        self.assertEqual(len(data["results"]), 2)
        # Checks that results are ordered by distance
        self.assertLess(
            data["results"][0]["distance"],
            data["results"][1]["distance"]
        )

    @patch('src.api.routes.search_documents')
    def test_search_documents_no_results(self, mock_search):
        """Tests search that returns no results."""
        mock_search.return_value = {
            "status": "success",
            "query": "nonexistent query",
            "total_results": 0,
            "results": [],
        }

        payload = {
            "query": "nonexistent query",
            "n_results": 5,
        }

        response = self.client.post("/search", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_results"], 0)

    @patch('src.api.routes.search_documents')
    def test_search_documents_failure(self, mock_search):
        """Tests failure in document search."""
        mock_search.return_value = {
            "status": "error",
            "message": "ChromaDB connection failed",
        }

        payload = {
            "query": "test query",
        }

        response = self.client.post("/search", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")

    @patch('src.api.routes.search_documents')
    def test_search_with_custom_n_results(self, mock_search):
        """Testa limitação customizada de resultados."""
        mock_search.return_value = {
            "status": "success",
            "query": "test",
            "total_results": 1,
            "results": [{"chunk_id": "test"}],
        }

        payload = {
            "query": "test",
            "n_results": 10,
        }

        response = self.client.post("/search", json=payload)

        self.assertEqual(response.status_code, 200)
        # Verifica que n_results foi passado ao search_documents
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        self.assertEqual(call_args.kwargs["n_results"], 10)


if __name__ == '__main__':
    unittest.main()

