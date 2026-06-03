from unittest.mock import MagicMock, patch

from src.services.agent import chat_nesy_agent


@patch("src.services.agent.ensure_model")
@patch("src.services.agent.get_prompt", return_value="prompt de sistema")
@patch("src.services.agent.get_ollama_client")
def test_chat_agent_sem_tool_calls(mock_get_client, mock_get_prompt, mock_ensure_model):
    client = MagicMock()
    client.chat.return_value = {
        "message": {"content": "Resposta direta sem tools"}
    }
    mock_get_client.return_value = client

    resposta = chat_nesy_agent("Pergunta simples")

    assert resposta == "Resposta direta sem tools"
    mock_ensure_model.assert_called_once()
    mock_get_prompt.assert_called_once_with("llm.system_prompt", "")
    client.chat.assert_called_once()


@patch("src.services.agent.pesquisar_opiniao_comunidade", return_value="opiniao ok")
@patch("src.services.agent.consultar_estatisticas_skin", return_value="stats ok")
@patch("src.services.agent.ensure_model")
@patch("src.services.agent.get_prompt", return_value="prompt de sistema")
@patch("src.services.agent.get_ollama_client")
def test_chat_agent_tool_call_sql(
    mock_get_client,
    mock_get_prompt,
    mock_ensure_model,
    mock_consultar,
    mock_pesquisar,
):
    client = MagicMock()
    client.chat.side_effect = [
        {
            "message": {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "consultar_estatisticas_skin",
                            "arguments": {"nome_skin": "AK-47 | Vulcan"},
                        }
                    }
                ],
            }
        },
        {"message": {"content": "Resposta final com base em SQL"}},
    ]
    mock_get_client.return_value = client

    resposta = chat_nesy_agent("Qual é o preço médio da AK-47 | Vulcan?")

    assert resposta == "Resposta final com base em SQL"
    assert client.chat.call_count == 2
    mock_consultar.assert_called_once_with(nome_skin="AK-47 | Vulcan")
    mock_pesquisar.assert_not_called()
    mock_ensure_model.assert_called_once()
    mock_get_prompt.assert_called_once_with("llm.system_prompt", "")


@patch("src.services.agent.pesquisar_opiniao_comunidade", return_value="opiniao ok")
@patch("src.services.agent.consultar_estatisticas_skin", return_value="stats ok")
@patch("src.services.agent.ensure_model")
@patch("src.services.agent.get_prompt", return_value="prompt de sistema")
@patch("src.services.agent.get_ollama_client")
def test_chat_agent_tool_call_opiniao(
    mock_get_client,
    mock_get_prompt,
    mock_ensure_model,
    mock_consultar,
    mock_pesquisar,
):
    client = MagicMock()
    client.chat.side_effect = [
        {
            "message": {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "pesquisar_opiniao_comunidade",
                            "arguments": {"topico": "AK-47 | Vulcan"},
                        }
                    }
                ],
            }
        },
        {"message": {"content": "Resposta final com base em opiniao"}},
    ]
    mock_get_client.return_value = client

    resposta = chat_nesy_agent("O que a comunidade acha da AK-47 | Vulcan?")

    assert resposta == "Resposta final com base em opiniao"
    assert client.chat.call_count == 2
    mock_pesquisar.assert_called_once_with(topico="AK-47 | Vulcan")
    mock_consultar.assert_not_called()
    mock_ensure_model.assert_called_once()
    mock_get_prompt.assert_called_once_with("llm.system_prompt", "")


@patch("src.services.agent.pesquisar_opiniao_comunidade", return_value="opiniao ok")
@patch("src.services.agent.consultar_estatisticas_skin", return_value="stats ok")
@patch("src.services.agent.ensure_model")
@patch("src.services.agent.get_prompt", return_value="prompt de sistema")
@patch("src.services.agent.get_ollama_client")
def test_chat_agent_tool_calls_analitico(
    mock_get_client,
    mock_get_prompt,
    mock_ensure_model,
    mock_consultar,
    mock_pesquisar,
):
    client = MagicMock()
    client.chat.side_effect = [
        {
            "message": {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "consultar_estatisticas_skin",
                            "arguments": {"nome_skin": "AK-47 | Vulcan"},
                        }
                    },
                    {
                        "function": {
                            "name": "pesquisar_opiniao_comunidade",
                            "arguments": {"topico": "AK-47 | Vulcan"},
                        }
                    },
                ],
            }
        },
        {"message": {"content": "Resposta final com SQL + RAG"}},
    ]
    mock_get_client.return_value = client

    resposta = chat_nesy_agent("Vale a pena comprar AK-47 | Vulcan agora?")

    assert resposta == "Resposta final com SQL + RAG"
    assert client.chat.call_count == 2
    mock_consultar.assert_called_once_with(nome_skin="AK-47 | Vulcan")
    mock_pesquisar.assert_called_once_with(topico="AK-47 | Vulcan")
    mock_ensure_model.assert_called_once()
    mock_get_prompt.assert_called_once_with("llm.system_prompt", "")


@patch("src.services.agent.pesquisar_opiniao_comunidade", return_value="opiniao ok")
@patch("src.services.agent.consultar_estatisticas_skin", return_value="stats ok")
@patch("src.services.agent.ensure_model")
@patch("src.services.agent.get_prompt", return_value="prompt de sistema")
@patch("src.services.agent.get_ollama_client")
def test_chat_agent_fallback_tool_call_in_content(
    mock_get_client,
    mock_get_prompt,
    mock_ensure_model,
    mock_consultar,
    mock_pesquisar,
):
    client = MagicMock()
    client.chat.side_effect = [
        {
            "message": {
                "content": (
                    '{"name":"consultar_estatisticas_skin",'
                    '"arguments":{"nome_skin":"AK-47 | Vulcan"}}'
                )
            }
        },
        {"message": {"content": "Resposta final com fallback"}},
    ]
    mock_get_client.return_value = client

    resposta = chat_nesy_agent("diz stats")

    assert resposta == "Resposta final com fallback"
    assert client.chat.call_count == 2
    mock_consultar.assert_called_once_with(nome_skin="AK-47 | Vulcan")
    mock_pesquisar.assert_not_called()
    mock_ensure_model.assert_called_once()
    mock_get_prompt.assert_called_once_with("llm.system_prompt", "")


@patch(
    "src.services.agent.consultar_estatisticas_skin",
    return_value="Dados exatos de mercado para a skin 'AK-47 | Vulcan'.",
)
@patch("src.services.agent.ensure_model")
@patch("src.services.agent.get_prompt", return_value="prompt de sistema")
@patch("src.services.agent.get_ollama_client")
def test_chat_agent_force_sql_route(
    mock_get_client,
    mock_get_prompt,
    mock_ensure_model,
    mock_consultar,
):
    client = MagicMock()
    client.chat.return_value = {
        "message": {"content": "Dados exatos de mercado para a skin 'AK-47 | Vulcan'."}
    }
    mock_get_client.return_value = client

    resposta = chat_nesy_agent(
        "I want SQL exact data only for skin AK-47 | Vulcan: min max mean quantity sold."
    )

    assert "Dados exatos de mercado" in resposta
    mock_consultar.assert_called_once_with(nome_skin="AK-47 | Vulcan")
    client.chat.assert_called_once()
    mock_ensure_model.assert_called_once()
    mock_get_prompt.assert_called_once_with("llm.system_prompt", "")
    mock_get_client.assert_called_once()