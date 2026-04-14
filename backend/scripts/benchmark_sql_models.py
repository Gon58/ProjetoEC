"""Benchmark SQL-focused LLM tool-calling across multiple Ollama models.

For each model, this script:
1. Ensures the model is available (pulls if missing).
2. Asks 3 SQL-focused questions that should route to PostgreSQL stats.
3. Runs the expected SQL query directly for ground truth.
4. Stores timings, outputs, and SQL reference values into a CSV file.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg


PROJECT_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_BACKEND_ROOT))

from src.core.config import POSTGRES_URL
from src.core.prompts import get_prompt
from src.services.embeddings import ensure_model, get_ollama_client
from src.services.tools import consultar_estatisticas_skin


def _clean_postgres_url(url: str | None) -> str:
    if not url:
        raise RuntimeError("POSTGRES_URL is not configured")
    return url.replace("postgresql+psycopg://", "postgresql://")


def _fetch_default_skin_names(limit: int = 3) -> list[str]:
    query = """
        SELECT name
        FROM skin
        WHERE source = 'skinport'
        ORDER BY id ASC
        LIMIT %s
    """
    with psycopg.connect(_clean_postgres_url(POSTGRES_URL)) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            rows = cur.fetchall()
    return [row[0] for row in rows if row and row[0]]


def _expected_sql_stats(skin_name: str) -> dict[str, Any]:
    query = """
        SELECT min_price, max_price, mean_price, quantity_sold, currency
        FROM skin
        WHERE name = %s
        LIMIT 1
    """
    with psycopg.connect(_clean_postgres_url(POSTGRES_URL)) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (skin_name,))
            row = cur.fetchone()

    if not row:
        return {"found": False}

    min_price, max_price, mean_price, quantity_sold, currency = row
    return {
        "found": True,
        "min_price": float(min_price) if min_price is not None else None,
        "max_price": float(max_price) if max_price is not None else None,
        "mean_price": float(mean_price) if mean_price is not None else None,
        "quantity_sold": int(quantity_sold) if quantity_sold is not None else None,
        "currency": currency,
    }


def _build_questions(skin_names: list[str]) -> list[dict[str, str]]:
    templates = [
        "Quero dados exatos via SQL da skin '{skin}': min, max, mean e quantity sold.",
        "Usa apenas SQL/PostgreSQL para a skin '{skin}' e devolve min, max, mean e quantidade vendida.",
        "Para a skin '{skin}', responde so com dados exatos de SQL: preco minimo, maximo, medio e quantity sold.",
    ]
    return [
        {
            "question_id": f"q{idx + 1}",
            "skin_name": skin,
            "question": templates[idx].format(skin=skin),
        }
        for idx, skin in enumerate(skin_names)
    ]


def _run_question(model: str, question: str) -> dict[str, Any]:
    client = get_ollama_client()
    system_prompt = get_prompt("llm.system_prompt", "") + (
        "\n\nNeste benchmark usa APENAS a ferramenta consultar_estatisticas_skin "
        "para dados de mercado. Nao uses opinioes/RAG."
    )

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    started = time.perf_counter()
    first = client.chat(model=model, messages=messages, tools=[consultar_estatisticas_skin])

    tool_calls = first.get("message", {}).get("tool_calls") or []
    tool_called = False
    tool_arguments = ""
    tool_output = ""

    messages.append(first["message"])

    if tool_calls:
        for tool_call in tool_calls:
            fn = tool_call.get("function", {})
            if fn.get("name") != "consultar_estatisticas_skin":
                continue

            tool_called = True
            args = fn.get("arguments", {})
            tool_arguments = str(args)

            try:
                tool_output = consultar_estatisticas_skin(**args)
            except Exception as exc:  # pragma: no cover - benchmark fallback
                tool_output = f"tool_error: {exc}"

            messages.append(
                {
                    "role": "tool",
                    "name": "consultar_estatisticas_skin",
                    "content": tool_output,
                }
            )

    if tool_called:
        final = client.chat(model=model, messages=messages)
        answer = final.get("message", {}).get("content", "")
    else:
        answer = first.get("message", {}).get("content", "")

    elapsed = time.perf_counter() - started

    return {
        "tool_called": tool_called,
        "tool_arguments": tool_arguments,
        "tool_output": tool_output,
        "answer": answer,
        "elapsed_seconds": round(elapsed, 4),
    }


def _parse_models(raw_models: str) -> list[str]:
    models = [m.strip() for m in raw_models.split(",") if m.strip()]
    if not models:
        raise RuntimeError("At least one model must be provided")
    return models


def _build_output_path(path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg)

    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return PROJECT_BACKEND_ROOT / "artifacts" / f"sql_model_benchmark_{stamp}.csv"


def _write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "timestamp_utc",
        "model",
        "pull_seconds",
        "error",
        "question_id",
        "skin_name",
        "question",
        "tool_called",
        "tool_arguments",
        "tool_output",
        "answer",
        "elapsed_seconds",
        "expected_found",
        "expected_min_price",
        "expected_max_price",
        "expected_mean_price",
        "expected_quantity_sold",
        "expected_currency",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark SQL tool-calling for multiple LLM models")
    parser.add_argument(
        "--models",
        required=True,
        help="Comma-separated model list, e.g. llama3.1,llama3.2:3b",
    )
    parser.add_argument(
        "--skin-names",
        default="",
        help="Optional comma-separated skin names. If omitted, picks 3 from PostgreSQL.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional CSV output path.",
    )
    args = parser.parse_args()

    models = _parse_models(args.models)
    if args.skin_names.strip():
        skin_names = [s.strip() for s in args.skin_names.split(",") if s.strip()]
    else:
        skin_names = _fetch_default_skin_names(limit=3)

    if len(skin_names) < 3:
        raise RuntimeError("Need at least 3 skin names to generate benchmark questions")

    questions = _build_questions(skin_names[:3])
    rows: list[dict[str, Any]] = []

    for model in models:
        pull_seconds = 0.0
        model_error = ""
        pull_start = time.perf_counter()
        try:
            ensure_model(model)
            pull_seconds = round(time.perf_counter() - pull_start, 4)
        except Exception as exc:
            model_error = str(exc)
            pull_seconds = round(time.perf_counter() - pull_start, 4)

        for question_data in questions:
            expected = _expected_sql_stats(question_data["skin_name"])
            result = {
                "tool_called": False,
                "tool_arguments": "",
                "tool_output": "",
                "answer": "",
                "elapsed_seconds": 0.0,
            }
            question_error = model_error

            if not model_error:
                try:
                    result = _run_question(model=model, question=question_data["question"])
                except Exception as exc:
                    question_error = str(exc)

            rows.append(
                {
                    "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                    "model": model,
                    "pull_seconds": pull_seconds,
                    "error": question_error,
                    "question_id": question_data["question_id"],
                    "skin_name": question_data["skin_name"],
                    "question": question_data["question"],
                    "tool_called": result["tool_called"],
                    "tool_arguments": result["tool_arguments"],
                    "tool_output": result["tool_output"],
                    "answer": result["answer"],
                    "elapsed_seconds": result["elapsed_seconds"],
                    "expected_found": expected.get("found", False),
                    "expected_min_price": expected.get("min_price"),
                    "expected_max_price": expected.get("max_price"),
                    "expected_mean_price": expected.get("mean_price"),
                    "expected_quantity_sold": expected.get("quantity_sold"),
                    "expected_currency": expected.get("currency"),
                }
            )

            print(
                f"model={model} question={question_data['question_id']} "
                f"tool_called={result['tool_called']} elapsed={result['elapsed_seconds']}s "
                f"error={'yes' if question_error else 'no'}"
            )

    output_path = _build_output_path(args.output or None)
    _write_csv(rows, output_path)
    print(f"Benchmark completed. CSV written to: {output_path}")


if __name__ == "__main__":
    main()
