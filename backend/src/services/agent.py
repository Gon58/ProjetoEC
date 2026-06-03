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
    """Emits a structured JSON log entry for a named agent lifecycle event."""
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

# Qwen2.5 occasionally emits its internal chat-template tokens literally in
# generated output.  Strip them before returning any text to callers.
_SPECIAL_TOKEN_RE = re.compile(r"<\|[^|>]+\|>")


def _clean_response(text: str) -> str:
    """Strips model special tokens and normalises whitespace in LLM output."""
    text = _SPECIAL_TOKEN_RE.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_system_prompt() -> str:
    """Loads the LLM system prompt from prompts.yaml (result is cached by get_prompt)."""
    return get_prompt("llm.system_prompt", "")


def _extract_tool_call_from_content(content: str | None) -> dict[str, Any] | None:
    """Extracts a tool call payload if the model returns JSON in plain text."""
    if not content:
        return None

    text = content.strip()
    if not text:
        return None

    candidates: list[str] = [text]

    # Some model responses wrap JSON in custom tags, e.g. <tool_call>...</tool_call>.
    tagged_blocks = re.findall(r"<tool_call>(.*?)</tool_call>", text, flags=re.DOTALL)
    candidates.extend(block.strip() for block in tagged_blocks if block.strip())

    # If content includes additional prose, also try the first JSON object-like block.
    json_like = re.search(r"\{[\s\S]*\}", text)
    if json_like:
        candidates.append(json_like.group(0).strip())

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue

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

def chat_nesy_agent(
    mensagem_utilizador: str,
    history: list[dict] | None = None,
) -> str:
    """Routes a user message through the NeSy agent pipeline and returns a response.

    Decides whether to call the SQL tool (exact market data), the RAG tool
    (community opinions), both, or neither, then synthesises a final answer
    using the LLM.  Conversation history is prepended to the message list so
    the model can resolve follow-up questions correctly.

    Args:
        mensagem_utilizador: The current user message (stripped before use).
        history: Optional list of prior turns as {role, content} dicts,
                 oldest first.  Sourced from the frontend chat state.

    Returns:
        A plain-text Portuguese response ready to display in the chat UI.
    """

    mensagem_utilizador = mensagem_utilizador.strip()
    if not mensagem_utilizador:
        return "Por favor, escreve uma pergunta."

    _log_event("agent_input", {"message": mensagem_utilizador, "model": LLM_MODEL})
    ensure_model(LLM_MODEL)

    client = get_ollama_client()
    system_prompt = load_system_prompt()

    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    for turn in history or []:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": mensagem_utilizador})
    
    ferramentas_disponiveis = {
        "consultar_estatisticas_skin": consultar_estatisticas_skin,
        "pesquisar_opiniao_comunidade": pesquisar_opiniao_comunidade
    }
    
    logger.info("agent_routing: %s", mensagem_utilizador)

    if _should_force_sql_route(mensagem_utilizador):
        extracted_skin = _extract_skin_name_for_sql(mensagem_utilizador)
        if extracted_skin:
            _log_event(
                "agent_force_sql_route",
                {"message": mensagem_utilizador, "skin": extracted_skin},
            )
            resultado_sql = consultar_estatisticas_skin(nome_skin=extracted_skin)
            _log_event(
                "agent_tool_result",
                {
                    "tool": "consultar_estatisticas_skin",
                    "result": str(resultado_sql),
                    "message": mensagem_utilizador,
                },
            )
            # Mirror the structure the normal path produces so the model
            # sees: user → assistant(tool_calls) → tool → assistant(response)
            messages.append({
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "function": {
                        "name": "consultar_estatisticas_skin",
                        "arguments": {"nome_skin": extracted_skin},
                    }
                }],
            })
            messages.append({
                "role": "tool",
                "content": str(resultado_sql),
                "name": "consultar_estatisticas_skin",
            })
            resposta_final = _chat_with_timeout(client, model=LLM_MODEL, messages=messages)
            resposta_texto = _clean_response(resposta_final["message"]["content"])
            _log_event("agent_output", {"message": mensagem_utilizador, "output": resposta_texto})
            return resposta_texto
    
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
            
            _log_event(
                "agent_tool_selected",
                {"tool": nome_da_tool, "arguments": argumentos, "message": mensagem_utilizador},
            )
            
            funcao_python = ferramentas_disponiveis.get(nome_da_tool)
            if not funcao_python:
                logger.warning("agent unknown tool requested: %s", nome_da_tool)
                continue

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
                "name": nome_da_tool,
            })
                
        # resposta final
        resposta_final = _chat_with_timeout(
            client,
            model=LLM_MODEL,
            messages=messages
        )
        resposta_texto = _clean_response(resposta_final["message"]["content"])
        _log_event("agent_output", {"message": mensagem_utilizador, "output": resposta_texto})
        return resposta_texto

    resposta_texto = _clean_response(resposta_llm["message"]["content"])
    _log_event("agent_output", {"message": mensagem_utilizador, "output": resposta_texto})
    return resposta_texto
