"""Profiles the chat query pipeline and prints per-phase timings.

This script mirrors the `/chat` pipeline with explicit phase timers and prints
named timings such as:
- ensure_model
- forced_sql_tool (when applicable)
- llm_router_call
- tool_sql_call / tool_rag_call
- llm_final_call

Usage:
    python scripts/profile_query_pipeline.py --query "..."
    python scripts/profile_query_pipeline.py --query "..." --runs 3
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PhaseEvent:
    """Represents a timed phase execution."""

    phase: str
    run: int
    elapsed_ms: float


def _build_parser() -> argparse.ArgumentParser:
    """Builds CLI args for query profiling."""
    parser = argparse.ArgumentParser(description="Profile chat query pipeline phases")
    parser.add_argument("--query", required=True, help="Query text to send through chat pipeline")
    parser.add_argument("--runs", type=int, default=1, help="Number of profiling runs")
    parser.add_argument(
        "--print-answer",
        action="store_true",
        help="Print the final answer text for each run",
    )
    return parser


def _record_phase(
    events: list[PhaseEvent], run_idx: int, phase: str, fn: Any, *args: Any, **kwargs: Any
) -> Any:
    """Runs a callable and records elapsed time under a named phase."""
    start = time.perf_counter()
    try:
        return fn(*args, **kwargs)
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        events.append(PhaseEvent(phase=phase, run=run_idx, elapsed_ms=elapsed_ms))


def _print_summary(events: list[PhaseEvent], total_ms_by_run: list[float]) -> None:
    """Prints per-phase stats and total pipeline time by run."""
    grouped: dict[str, list[float]] = defaultdict(list)
    for event in events:
        grouped[event.phase].append(event.elapsed_ms)

    print("\n=== Pipeline Totals (per run) ===")
    for idx, total in enumerate(total_ms_by_run, start=1):
        print(f"run_{idx}: {total:.2f} ms")

    print("\n=== Phase Timings (aggregated) ===")
    for phase in sorted(grouped.keys()):
        values = grouped[phase]
        avg = sum(values) / len(values)
        print(
            f"{phase}: count={len(values)} avg={avg:.2f} ms "
            f"min={min(values):.2f} ms max={max(values):.2f} ms"
        )


def main() -> None:
    """Profiles a query using the same high-level chat pipeline as `/chat`."""
    args = _build_parser().parse_args()
    if args.runs < 1:
        raise SystemExit("--runs must be >= 1")

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.services import agent as agent_module  # noqa: E402

    events: list[PhaseEvent] = []
    total_ms_by_run: list[float] = []

    for run_idx in range(1, args.runs + 1):
        start_total = time.perf_counter()

        _record_phase(
            events,
            run_idx,
            "ensure_model",
            agent_module.ensure_model,
            agent_module.LLM_MODEL,
        )

        if agent_module._should_force_sql_route(args.query):
            extracted_skin = agent_module._extract_skin_name_for_sql(args.query)
            if extracted_skin:
                answer = _record_phase(
                    events,
                    run_idx,
                    "forced_sql_tool",
                    agent_module.consultar_estatisticas_skin,
                    nome_skin=extracted_skin,
                )
            else:
                answer = "Nao foi possivel extrair nome de skin para rota SQL forcada."
        else:
            client = agent_module.get_ollama_client()
            system_prompt = agent_module.load_system_prompt()
            mensagens = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": args.query},
            ]

            resposta_llm = _record_phase(
                events,
                run_idx,
                "llm_router_call",
                agent_module._chat_with_timeout,
                client,
                model=agent_module.LLM_MODEL,
                messages=mensagens,
                tools=[
                    agent_module.consultar_estatisticas_skin,
                    agent_module.pesquisar_opiniao_comunidade,
                ],
            )

            mensagens.append(resposta_llm["message"])
            tool_calls = resposta_llm.get("message", {}).get("tool_calls") or []

            if not tool_calls:
                fallback = agent_module._extract_tool_call_from_content(
                    resposta_llm.get("message", {}).get("content")
                )
                if fallback:
                    tool_calls = [{"function": fallback}]

            if tool_calls:
                ferramentas = {
                    "consultar_estatisticas_skin": agent_module.consultar_estatisticas_skin,
                    "pesquisar_opiniao_comunidade": agent_module.pesquisar_opiniao_comunidade,
                }

                for tool_call in tool_calls:
                    nome_tool = tool_call["function"]["name"]
                    argumentos = tool_call["function"]["arguments"]
                    func = ferramentas.get(nome_tool)
                    if not func:
                        continue

                    phase_name = (
                        "tool_sql_call"
                        if nome_tool == "consultar_estatisticas_skin"
                        else "tool_rag_call"
                    )
                    resultado_tool = _record_phase(
                        events,
                        run_idx,
                        phase_name,
                        func,
                        **argumentos,
                    )
                    mensagens.append(
                        {
                            "role": "tool",
                            "content": str(resultado_tool),
                            "name": nome_tool,
                        }
                    )

                resposta_final = _record_phase(
                    events,
                    run_idx,
                    "llm_final_call",
                    agent_module._chat_with_timeout,
                    client,
                    model=agent_module.LLM_MODEL,
                    messages=mensagens,
                )
                answer = resposta_final["message"]["content"]
            else:
                answer = resposta_llm["message"]["content"]

        total_elapsed_ms = (time.perf_counter() - start_total) * 1000
        total_ms_by_run.append(total_elapsed_ms)

        if args.print_answer:
            print(f"\n--- Answer run_{run_idx} ---")
            print(answer)

    _print_summary(events, total_ms_by_run)


if __name__ == "__main__":
    main()
