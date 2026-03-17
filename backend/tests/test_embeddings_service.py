"""Testes unitarios para disponibilidade/autostart do Ollama no servico de embeddings."""

import unittest
from unittest.mock import patch

from src.services import embeddings


class _BrokenClient:
    def list(self):
        raise RuntimeError("connection refused")


class _WorkingClient:
    def list(self):
        return {"models": []}


class TestEmbeddingsService(unittest.TestCase):
    """Valida comportamento de recover automatico do Ollama."""

    @patch("src.services.embeddings.time.sleep", return_value=None)
    @patch("src.services.embeddings.time.time")
    @patch("src.services.embeddings._start_ollama_service_if_possible", return_value=True)
    @patch("src.services.embeddings.get_ollama_client")
    def test_ensure_ollama_available_recovers_after_start_attempt(
        self,
        mock_get_client,
        _mock_start,
        mock_time,
        _mock_sleep,
    ):
        """Primeira tentativa falha e segunda passa apos tentativa de start."""
        mock_get_client.side_effect = [_BrokenClient(), _WorkingClient()]
        mock_time.side_effect = [0, 1]

        embeddings.ensure_ollama_available()

        self.assertEqual(mock_get_client.call_count, 2)

    @patch("src.services.embeddings.time.sleep", return_value=None)
    @patch("src.services.embeddings.time.time")
    @patch("src.services.embeddings._start_ollama_service_if_possible", return_value=False)
    @patch("src.services.embeddings.get_ollama_client", return_value=_BrokenClient())
    def test_ensure_ollama_available_raises_after_timeout(
        self,
        _mock_get_client,
        _mock_start,
        mock_time,
        _mock_sleep,
    ):
        """Se continuar indisponivel ate timeout, deve levantar erro claro."""
        timeout = embeddings.OLLAMA_START_TIMEOUT_SECONDS
        mock_time.side_effect = [0, timeout + 1]

        with self.assertRaises(RuntimeError):
            embeddings.ensure_ollama_available()


if __name__ == "__main__":
    unittest.main()
