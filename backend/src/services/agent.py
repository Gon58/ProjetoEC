import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any

from ..core.config import LLM_MODEL, OLLAMA_TIMEOUT_SECONDS
from ..core.prompts import get_prompt
from .embeddings import ensure_model, get_ollama_client
from .tools import consultar_estatisticas_skin, pesquisar_opiniao_comunidade

logger = logging.getLogger(__name__)


def _log_event(event: str, payload: dict[str, Any]) -> None:
    logger.info(json.dumps({"event": event, **payload}, ensure_ascii=False, default=str))


def _chat_with_timeout(client: Any, **kwargs: Any) -> dict[str, Any]:
    """Executes an Ollama chat call with timeout to avoid indefinite blocking."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(client.chat, **kwargs)
        try:
            return future.result(timeout=OLLAMA_TIMEOUT_SECONDS)
        except FutureTimeoutError as exc:
            raise RuntimeError(
                f"Ollama chat request exceeded timeout of {OLLAMA_TIMEOUT_SECONDS} seconds"
            ) from exc

def load_system_prompt() -> str:
    return get_prompt("llm.system_prompt", "")


def _extract_tool_call_from_content(content: str | None) -> dict[str, Any] | None:
    """Extracts a tool call payload if the model returns JSON in plain text."""
    if not content:
        return None

    text = content.strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
    except Exception:
        return None

    if isinstance(parsed, dict):
        name = parsed.get("name")
        arguments = parsed.get("arguments")
        if isinstance(name, str) and isinstance(arguments, dict):
            return {"name": name, "arguments": arguments}

    return None


def _should_force_sql_route(mensagem_utilizador: str) -> bool:
    """Forces SQL route for explicit exact-data requests."""
    text = mensagem_utilizador.lower()
    requires_sql = any(token in text for token in ("sql", "exact", "exatos", "dados exatos"))
    asks_metrics = any(
        token in text
        for token in (
            "min",
            "max",
            "mean",
            "médio",
            "medio",
            "quantidade",
            "quantity",
            "vendida",
            "sold",
        )
    )
    return requires_sql and asks_metrics


def _extract_skin_name_for_sql(mensagem_utilizador: str) -> str | None:
    """Extracts a skin name from explicit SQL-only queries."""
    patterns = [
        r"skin\s+(.+?)(?::|$)",
        r"skin\s+['\"](.+?)['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, mensagem_utilizador, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            return name if name else None
    return None

def chat_nesy_agent(mensagem_utilizador: str) -> str:
    """
    Main NeSy router.
    """

    print(f"A verificar/instalar o modelo {LLM_MODEL} no Docker...")
    _log_event("agent_input", {"message": mensagem_utilizador, "model": LLM_MODEL})
    ensure_model(LLM_MODEL)
    
    client = get_ollama_client()
    system_prompt = load_system_prompt()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": mensagem_utilizador}
    ]
    
    ferramentas_disponiveis = {
        "consultar_estatisticas_skin": consultar_estatisticas_skin,
        "pesquisar_opiniao_comunidade": pesquisar_opiniao_comunidade
    }
    
    print(f"\n[Agente] A analisar a pergunta: '{mensagem_utilizador}'")

    if _should_force_sql_route(mensagem_utilizador):
        extracted_skin = _extract_skin_name_for_sql(mensagem_utilizador)
        if extracted_skin:
            _log_event(
                "agent_force_sql_route",
                {"message": mensagem_utilizador, "skin": extracted_skin},
            )
            resultado_sql = consultar_estatisticas_skin(nome_skin=extracted_skin)
            _log_event("agent_output", {"message": mensagem_utilizador, "output": resultado_sql})
            return resultado_sql
    
    # router
    resposta_llm = _chat_with_timeout(
        client,
        model=LLM_MODEL,
        messages=messages,
        tools=[consultar_estatisticas_skin, pesquisar_opiniao_comunidade]
    )
    
    messages.append(resposta_llm["message"])
    
    # verificar se o LLM decidiu chamar alguma ferramenta
    tool_calls = resposta_llm.get("message", {}).get("tool_calls") or []
    if not tool_calls:
        fallback = _extract_tool_call_from_content(resposta_llm.get("message", {}).get("content"))
        if fallback:
            tool_calls = [{"function": fallback}]

    if tool_calls:
        for tool_call in tool_calls:
            nome_da_tool = tool_call["function"]["name"]
            argumentos = tool_call["function"]["arguments"]
            
            print(f"[Router] O LLM escolheu a rota: {nome_da_tool}")
            _log_event(
                "agent_tool_selected",
                {"tool": nome_da_tool, "arguments": argumentos, "message": mensagem_utilizador},
            )
            
            funcao_python = ferramentas_disponiveis.get(nome_da_tool)
            if funcao_python:
                try:
                    resultado_bruto = funcao_python(**argumentos)
                except Exception as exc:
                    resultado_bruto = (
                        "Nao foi possível concluir a ferramenta neste momento; "
                        "responde com os dados disponiveis sem inventar valores."
                    )
                    _log_event(
                        "agent_tool_error",
                        {
                            "tool": nome_da_tool,
                            "error": str(exc),
                            "message": mensagem_utilizador,
                        },
                    )

                _log_event(
                    "agent_tool_result",
                    {
                        "tool": nome_da_tool,
                        "result": str(resultado_bruto),
                        "message": mensagem_utilizador,
                    },
                )
                
                messages.append({
                    "role": "tool",
                    "content": str(resultado_bruto),
                    "name": nome_da_tool
                })
                
        # resposta final
        resposta_final = _chat_with_timeout(
            client,
            model=LLM_MODEL,
            messages=messages
        )
        resposta_texto = resposta_final["message"]["content"]
        _log_event("agent_output", {"message": mensagem_utilizador, "output": resposta_texto})
        return resposta_texto
        
    resposta_texto = resposta_llm["message"]["content"]
    _log_event("agent_output", {"message": mensagem_utilizador, "output": resposta_texto})
    return resposta_texto
