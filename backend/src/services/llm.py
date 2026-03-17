"""
Servicos de geracao de resposta com LLM via Ollama.

Este modulo implementa a camada de geracao textual (Phase 2), separada da
recuperacao vetorial. Os prompts sao carregados a partir de ficheiros para
manter o codigo limpo e facilitar iteracao do comportamento.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from src.services.embeddings import ensure_model, get_ollama_client

DEFAULT_LLM_MODEL = "mistral"
DEFAULT_SYSTEM_PROMPT_FILE = "rag_system_prompt.txt"
DEFAULT_USER_PROMPT_FILE = "rag_user_prompt.txt"
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt_template(filename: str) -> str:
    """
    Carrega um template de prompt a partir de src/prompts.

    Args:
        filename: Nome do ficheiro de prompt.

    Returns:
        Conteudo textual do prompt, sem espacos extra no fim.

    Raises:
        FileNotFoundError: Se o ficheiro nao existir.
    """
    prompt_path = _PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def format_retrieval_context(search_results: Iterable[Mapping[str, Any]]) -> str:
    """
    Formata chunks recuperados para contexto do LLM.

    Cada item inclui distancia semantica para ajudar o modelo a priorizar
    evidencia mais forte (distancia menor = maior similaridade).

    Args:
        search_results: Iteravel de resultados com chaves como text, distance e metadata.

    Returns:
        String formatada pronta para injecao no prompt.
    """
    blocks: list[str] = []

    for index, result in enumerate(search_results, start=1):
        text = str(result.get("text", "")).strip()
        if not text:
            continue

        distance = result.get("distance")
        distance_text = "unknown"
        if isinstance(distance, (int, float)):
            distance_text = f"{float(distance):.6f}"

        metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
        doc_id = metadata.get("doc_id", "unknown")
        chunk_index = metadata.get("chunk_index", "unknown")

        block = (
            f"[Chunk {index}] distance={distance_text} | "
            f"doc_id={doc_id} | chunk_index={chunk_index}\n"
            f"{text}"
        )
        blocks.append(block)

    if not blocks:
        return "(sem contexto recuperado)"

    return "\n\n".join(blocks)


def generate_rag_response(
    query: str,
    search_results: Iterable[Mapping[str, Any]],
    *,
    model: str = DEFAULT_LLM_MODEL,
    system_prompt_file: str = DEFAULT_SYSTEM_PROMPT_FILE,
    user_prompt_file: str = DEFAULT_USER_PROMPT_FILE,
    temperature: float = 0.2,
    top_p: float = 0.9,
    max_tokens: int = 512,
) -> dict[str, Any]:
    """
    Gera resposta RAG usando resultados recuperados e modelo LLM no Ollama.

    Args:
        query: Pergunta do utilizador.
        search_results: Resultados da recuperacao vetorial (chunks + distance).
        model: Nome do modelo Ollama generativo (default: mistral).
        system_prompt_file: Ficheiro do system prompt em src/prompts.
        user_prompt_file: Ficheiro do template de prompt do utilizador.
        temperature: Temperatura de geracao.
        top_p: Parametro nucleus sampling.
        max_tokens: Limite de tokens de saida.

    Returns:
        Dicionario com status, answer, model e metadados de execucao.
    """
    try:
        ensure_model(model)

        system_prompt = load_prompt_template(system_prompt_file)
        user_prompt_template = load_prompt_template(user_prompt_file)

        context_block = format_retrieval_context(search_results)
        final_prompt = user_prompt_template.format(query=query.strip(), context=context_block)

        client = get_ollama_client()
        response = client.generate(
            model=model,
            prompt=final_prompt,
            system=system_prompt,
            options={
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens,
            },
        )

        return {
            "status": "success",
            "query": query,
            "model": model,
            "answer": response.get("response", "").strip(),
            "context_used": context_block,
            "system_prompt_file": system_prompt_file,
            "user_prompt_file": user_prompt_file,
            "done": bool(response.get("done", False)),
            "total_duration": response.get("total_duration"),
            "eval_count": response.get("eval_count"),
            "prompt_eval_count": response.get("prompt_eval_count"),
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "query": query,
            "model": model,
        }
