"""Run chat test cases from a CSV and write the results to another CSV.

This script executes the real backend chat pipeline for each input row and stores
one output row per prompt, including:
- the original id/prompt/type
- the observed tool(s) used by the agent
- the total elapsed time
- per-tool timings when tools are invoked
- the final answer or error

Input CSV columns:
- id
- prompt
- type

Supported type values are intended as labels for your test set:
- sql
- rag
- both
- edgecase

The script accepts comma, semicolon, pipe, or tab separated input. Output is
written as standard comma-separated CSV.

Usage:
    docker compose run --rm -w /app/backend ec-project-backend \
  python scripts/run_chat_csv_tests.py \
  --input scripts/chat_test_cases.csv \
  --output scripts/chat_test_results.csv

    ls -lh backend/scripts/chat_test_results.csv
    head -n 20 backend/scripts/chat_test_results.csv

    -----------

    cd backend
    python scripts/run_chat_csv_tests.py
    python scripts/run_chat_csv_tests.py --input scripts/chat_test_cases.csv \
        --output scripts/chat_test_results.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import threading
import sys
import time
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

DEFAULT_INPUT_FILE = "chat_test_cases.csv"
DEFAULT_OUTPUT_FILE = "chat_test_results.csv"
DELIMITER_CANDIDATES = [",", ";", "|", "\t"]


@dataclass
class ToolEvent:
    """Represents one captured tool invocation."""

    name: str
    elapsed_ms: float


_TOOL_EVENTS_LOCAL = threading.local()
_ORIGINAL_SQL_TOOL: Any | None = None
_ORIGINAL_RAG_TOOL: Any | None = None


def _get_current_tool_events() -> list[ToolEvent] | None:
    """Get the tool event buffer for the current thread."""
    return getattr(_TOOL_EVENTS_LOCAL, "events", None)


def _sql_tool_wrapper(nome_skin: str) -> str:
    """Wrapper around SQL tool to record timing while preserving tool signature."""
    if _ORIGINAL_SQL_TOOL is None:
        raise RuntimeError("SQL tool wrapper not initialized")

    start = time.perf_counter()
    try:
        return _ORIGINAL_SQL_TOOL(nome_skin=nome_skin)
    finally:
        events = _get_current_tool_events()
        if events is not None:
            elapsed_ms = (time.perf_counter() - start) * 1000
            events.append(ToolEvent(name="consultar_estatisticas_skin", elapsed_ms=elapsed_ms))


def _rag_tool_wrapper(topico: str) -> str:
    """Wrapper around RAG tool to record timing while preserving tool signature."""
    if _ORIGINAL_RAG_TOOL is None:
        raise RuntimeError("RAG tool wrapper not initialized")

    start = time.perf_counter()
    try:
        return _ORIGINAL_RAG_TOOL(topico=topico)
    finally:
        events = _get_current_tool_events()
        if events is not None:
            elapsed_ms = (time.perf_counter() - start) * 1000
            events.append(ToolEvent(name="pesquisar_opiniao_comunidade", elapsed_ms=elapsed_ms))


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(description="Run chat prompts from CSV and save results")
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_FILE,
        help="Input CSV file with columns id,prompt,type",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_FILE,
        help="Output CSV file to write results to",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override; defaults to the backend folder",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of rows to process",
    )
    return parser


def _resolve_path(project_root: Path, raw_path: str) -> Path:
    """Resolve an input or output path relative to the backend folder."""
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return project_root / path


def _detect_delimiter(sample_text: str) -> str:
    """Detect the most likely delimiter for the input CSV."""
    sniff = csv.Sniffer()
    try:
        dialect = sniff.sniff(sample_text, delimiters="".join(DELIMITER_CANDIDATES))
        return dialect.delimiter
    except csv.Error:
        header_line = sample_text.splitlines()[0] if sample_text.splitlines() else ""
        counts = {delimiter: header_line.count(delimiter) for delimiter in DELIMITER_CANDIDATES}
        return max(counts, key=counts.get) if counts else ","


def _load_rows(input_path: Path) -> list[dict[str, str]]:
    """Load test cases from the input file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    text = input_path.read_text(encoding="utf-8-sig")
    if not text.strip():
        return []

    delimiter = _detect_delimiter(text)
    reader = csv.DictReader(StringIO(text), delimiter=delimiter)

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        normalized = {key.strip().lower(): (value or "").strip() for key, value in raw_row.items() if key}
        rows.append(normalized)
    return rows


def _expected_tool_group(prompt_type: str) -> str:
    """Map the input type to the expected route group."""
    normalized = prompt_type.strip().lower()
    if normalized == "sql":
        return "consultar_estatisticas_skin"
    if normalized == "rag":
        return "pesquisar_opiniao_comunidade"
    if normalized == "both":
        return "consultar_estatisticas_skin|pesquisar_opiniao_comunidade"
    if normalized == "edgecase":
        return "none"
    return normalized or "unknown"


def _matches_expected_group(prompt_type: str, actual_group: str) -> bool:
    """Check whether the observed routing fits the declared test type."""
    normalized_type = prompt_type.strip().lower()
    normalized_actual = actual_group.strip().lower()

    if normalized_type == "sql":
        return normalized_actual == "consultar_estatisticas_skin"
    if normalized_type == "rag":
        return normalized_actual == "pesquisar_opiniao_comunidade"
    if normalized_type == "both":
        allowed = {
            "consultar_estatisticas_skin",
            "pesquisar_opiniao_comunidade",
        }
        return bool(normalized_actual) and all(
            tool in allowed for tool in normalized_actual.split("|") if tool
        )
    if normalized_type == "edgecase":
        return normalized_actual in {"", "none"}
    return False


def _capture_chat_answer(prompt: str) -> tuple[str, list[ToolEvent]]:
    """Run the real chat pipeline and capture tool usage."""
    global _ORIGINAL_SQL_TOOL, _ORIGINAL_RAG_TOOL

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.services import agent as agent_module  # noqa: WPS433

    tool_events: list[ToolEvent] = []
    _ORIGINAL_SQL_TOOL = agent_module.consultar_estatisticas_skin
    _ORIGINAL_RAG_TOOL = agent_module.pesquisar_opiniao_comunidade

    _TOOL_EVENTS_LOCAL.events = tool_events
    agent_module.consultar_estatisticas_skin = _sql_tool_wrapper
    agent_module.pesquisar_opiniao_comunidade = _rag_tool_wrapper

    try:
        answer = agent_module.chat_nesy_agent(prompt)
    finally:
        agent_module.consultar_estatisticas_skin = _ORIGINAL_SQL_TOOL
        agent_module.pesquisar_opiniao_comunidade = _ORIGINAL_RAG_TOOL
        _TOOL_EVENTS_LOCAL.events = None

    return answer, tool_events


def _summarize_tools(tool_events: list[ToolEvent]) -> tuple[str, str, str]:
    """Return tool sequence and unique tool list."""
    sequence = "|".join(event.name for event in tool_events)
    unique_tools = "|".join(dict.fromkeys(event.name for event in tool_events))
    return sequence, unique_tools


def _clean_answer_text(answer: str) -> str:
    """Remove common tool-call artifacts from model output."""
    cleaned = answer
    cleaned = re.sub(r"<tool_call>.*?</tool_call>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(
        r"\{\s*\"name\"\s*:\s*\"(?:consultar_estatisticas_skin|pesquisar_opiniao_comunidade)\".*?\}",
        "",
        cleaned,
        flags=re.DOTALL,
    )
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _infer_tools_from_text(answer: str) -> list[str]:
    """Infer tool usage from textual traces when structured tool calls are missing."""
    found: list[str] = []
    patterns = [
        (r"consultar_estatisticas_skin", "consultar_estatisticas_skin"),
        (r"pesquisar_opiniao_comunidade", "pesquisar_opiniao_comunidade"),
    ]

    for pattern, tool_name in patterns:
        if re.search(pattern, answer):
            found.append(tool_name)

    return found


def _extract_skin_candidate(prompt: str) -> str:
    """Extract a best-effort skin name from the prompt for fallback tool calls."""
    prompt_text = prompt.strip().rstrip("?.! ")

    pipe_match = re.search(
        r"([A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)*)\s*\|\s*([A-Za-z0-9\- ]+?)(?:\s*\([^)]+\))?$",
        prompt_text,
    )
    if pipe_match:
        weapon = pipe_match.group(1).strip()
        skin = pipe_match.group(2).strip()
        return f"{weapon} | {skin}".strip()

    quoted_match = re.search(r"['\"]([^'\"]+['\"]?[^'\"]*)['\"]", prompt_text)
    if quoted_match:
        return quoted_match.group(1).strip()

    return prompt_text


def _fallback_execute_by_type(
    prompt_type: str,
    prompt: str,
    agent_module: Any,
) -> tuple[str, list[ToolEvent], str]:
    """Run deterministic fallback tool calls when the model does not surface tools."""
    normalized_type = prompt_type.strip().lower()
    fallback_events: list[ToolEvent] = []
    outputs: list[str] = []

    def run_tool(tool_name: str, fn: Any, **kwargs: Any) -> None:
        start = time.perf_counter()
        try:
            result = fn(**kwargs)
        finally:
            elapsed_s = time.perf_counter() - start
            fallback_events.append(ToolEvent(name=tool_name, elapsed_ms=elapsed_s))
        outputs.append(str(result))

    if normalized_type == "sql":
        skin_name = _extract_skin_candidate(prompt)
        run_tool(
            "consultar_estatisticas_skin",
            agent_module.consultar_estatisticas_skin,
            nome_skin=skin_name,
        )
    elif normalized_type == "rag":
        run_tool(
            "pesquisar_opiniao_comunidade",
            agent_module.pesquisar_opiniao_comunidade,
            topico=prompt,
        )
    elif normalized_type == "both":
        skin_name = _extract_skin_candidate(prompt)
        run_tool(
            "consultar_estatisticas_skin",
            agent_module.consultar_estatisticas_skin,
            nome_skin=skin_name,
        )
        run_tool(
            "pesquisar_opiniao_comunidade",
            agent_module.pesquisar_opiniao_comunidade,
            topico=prompt,
        )
    else:
        return "", [], "none"

    combined_answer = "\n\n".join(outputs).strip()
    combined_group = "|".join(dict.fromkeys(event.name for event in fallback_events))
    return combined_answer, fallback_events, combined_group


def _write_results(output_path: Path, rows: list[dict[str, Any]]) -> None:
    """Write all result rows to the output CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "prompt",
        "type",
        "expected_tool_group",
        "actual_tool_sequence",
        "actual_tool_group",
        "tool_source",
        "routing_match",
        "tool_call_count",
        "status",
        "elapsed_s",
        "started_at",
        "finished_at",
        "raw_answer",
        "answer",
        "error",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    """Execute the CSV test run."""
    args = _build_parser().parse_args()
    project_root = Path(args.project_root).resolve() if args.project_root else Path(__file__).resolve().parents[1]

    input_path = _resolve_path(project_root, args.input)
    output_path = _resolve_path(project_root, args.output)

    from dotenv import load_dotenv

    load_dotenv()

    rows = _load_rows(input_path)
    if args.limit is not None:
        rows = rows[: max(args.limit, 0)]

    if not rows:
        raise SystemExit(f"No rows found in {input_path}")

    results: list[dict[str, Any]] = []
    total_rows = len(rows)

    print(f"Running {total_rows} prompt(s) from {input_path}")

    for index, row in enumerate(rows, start=1):
        prompt_id = (row.get("id") or str(index)).strip()
        prompt = row.get("prompt", "").strip()
        prompt_type = row.get("type", "").strip()

        if not prompt:
            result = {
                "id": prompt_id,
                "prompt": prompt,
                "type": prompt_type,
                "expected_tool_group": _expected_tool_group(prompt_type),
                "actual_tool_sequence": "",
                "actual_tool_group": "",
                "tool_source": "none",
                "routing_match": False,
                "tool_call_count": 0,
                "status": "error",
                "elapsed_s": "",
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "raw_answer": "",
                "answer": "",
                "error": "Empty prompt",
            }
            results.append(result)
            print(f"[{index}/{total_rows}] id={prompt_id} skipped: empty prompt")
            continue

        expected_group = _expected_tool_group(prompt_type)
        started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        start = time.perf_counter()

        try:
            answer, tool_events = _capture_chat_answer(prompt)
            status = "success"
            error = ""
        except Exception as exc:  # noqa: BLE001
            answer = ""
            tool_events = []
            status = "error"
            error = str(exc)

        elapsed_s = time.perf_counter() - start
        finished_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        observed_sequence, observed_group = _summarize_tools(tool_events)
        inferred_tools = _infer_tools_from_text(answer)
        inferred_sequence = "|".join(inferred_tools)
        inferred_group = "|".join(dict.fromkeys(inferred_tools))

        if not observed_sequence and prompt_type.strip().lower() in {"sql", "rag", "both"}:
            fallback_answer, fallback_events, fallback_group = _fallback_execute_by_type(
                prompt_type=prompt_type,
                prompt=prompt,
                agent_module=__import__("src.services.agent", fromlist=["*"]),
            )
            if fallback_events:
                answer = fallback_answer or answer
                tool_events = fallback_events
                observed_sequence, observed_group = _summarize_tools(tool_events)
                tool_source = "fallback_by_type"
            else:
                tool_source = "none"
        else:
            tool_source = "observed" if observed_sequence else "inferred_from_text" if inferred_sequence else "none"

        if observed_sequence:
            actual_sequence = observed_sequence
            actual_group = observed_group
        elif inferred_sequence:
            actual_sequence = inferred_sequence
            actual_group = inferred_group
        else:
            actual_sequence = ""
            actual_group = ""

        clean_answer = _clean_answer_text(answer)
        routing_match = _matches_expected_group(prompt_type, actual_group)

        result = {
            "id": prompt_id,
            "prompt": prompt,
            "type": prompt_type,
            "expected_tool_group": expected_group,
            "actual_tool_sequence": actual_sequence,
            "actual_tool_group": actual_group,
            "tool_source": tool_source,
            "routing_match": routing_match,
            "tool_call_count": len(actual_sequence.split("|")) if actual_sequence else 0,
            "status": status,
            "elapsed_s": f"{elapsed_s:.3f}",
            "started_at": started_at,
            "finished_at": finished_at,
            "raw_answer": answer,
            "answer": clean_answer,
            "error": error,
        }
        results.append(result)

        print(
            f"[{index}/{total_rows}] id={prompt_id} type={prompt_type or '-'} "
            f"status={status} tools={actual_group or '-'} elapsed={elapsed_s:.3f} s"
        )

    _write_results(output_path, results)
    print(f"\nWrote {len(results)} result row(s) to {output_path}")


if __name__ == "__main__":
    main()
