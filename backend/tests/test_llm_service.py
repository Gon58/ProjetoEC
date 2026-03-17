"""Testes unitarios da camada LLM (prompts + formatacao de contexto + geracao)."""

import unittest
from unittest.mock import MagicMock, patch

from src.services.llm import format_retrieval_context, generate_rag_response


class TestLlmService(unittest.TestCase):
    """Valida comportamento base do servico LLM para RAG."""

    def test_format_retrieval_context_includes_distance_and_metadata(self):
        """Garante que o contexto inclui distancia, doc_id e chunk_index."""
        search_results = [
            {
                "text": "Primeira review relevante.",
                "distance": 0.1234567,
                "metadata": {"doc_id": "steam:1", "chunk_index": 0},
            },
            {
                "text": "Segunda review relevante.",
                "distance": 0.845,
                "metadata": {"doc_id": "steam:2", "chunk_index": 1},
            },
        ]

        context = format_retrieval_context(search_results)

        self.assertIn("distance=0.123457", context)
        self.assertIn("doc_id=steam:1", context)
        self.assertIn("chunk_index=0", context)
        self.assertIn("distance=0.845000", context)

    @patch("src.services.llm.ensure_model")
    @patch("src.services.llm.get_ollama_client")
    @patch("src.services.llm.load_prompt_template")
    def test_generate_rag_response_success(self, mock_load_prompt, mock_get_client, mock_ensure):
        """Garante resposta de sucesso com prompts externos e chamada ao Ollama."""
        mock_load_prompt.side_effect = [
            "System prompt content",
            "Pergunta: {query}\nContexto: {context}",
        ]

        mock_client = MagicMock()
        mock_client.generate.return_value = {
            "response": "Resposta final",
            "done": True,
            "total_duration": 123,
            "eval_count": 40,
            "prompt_eval_count": 120,
        }
        mock_get_client.return_value = mock_client

        result = generate_rag_response(
            query="Quais os problemas mais comuns?",
            search_results=[
                {
                    "text": "Muitos jogadores reportam cheaters.",
                    "distance": 0.42,
                    "metadata": {"doc_id": "steam:10", "chunk_index": 0},
                }
            ],
            model="mistral",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["answer"], "Resposta final")
        mock_ensure.assert_called_once_with("mistral")
        mock_client.generate.assert_called_once()

    @patch("src.services.llm.ensure_model", side_effect=RuntimeError("model unavailable"))
    def test_generate_rag_response_error(self, _mock_ensure):
        """Garante formato de erro consistente quando a geracao falha."""
        result = generate_rag_response(query="Teste", search_results=[], model="mistral")

        self.assertEqual(result["status"], "error")
        self.assertIn("model unavailable", result["message"])


if __name__ == "__main__":
    unittest.main()
