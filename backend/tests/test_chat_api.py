import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app


class TestChatAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("src.api.routes.chat_nesy_agent", return_value="Resposta do agente")
    def test_chat_success(self, mock_chat):
        payload = {"message": "Vale a pena comprar AK-47 | Vulcan?"}

        response = self.client.post("/chat", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["message"], payload["message"])
        self.assertEqual(body["answer"], "Resposta do agente")
        mock_chat.assert_called_once_with(payload["message"], history=[])

    @patch("src.api.routes.chat_nesy_agent", side_effect=RuntimeError("falha LLM"))
    def test_chat_failure(self, mock_chat):
        payload = {"message": "Pergunta qualquer"}

        response = self.client.post("/chat", json=payload)

        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["message"], payload["message"])
        self.assertEqual(
            body["answer"],
            "Nao foi possível processar a mensagem neste momento.",
        )
        mock_chat.assert_called_once_with(payload["message"], history=[])
