"""Quick RAG smoke test for retrieval + LLM generation.

Usage (from repository root):
    .venv\\Scripts\\python.exe backend\\src\\scripts\\rag_smoke_test.py

Optional custom query:
    .venv\\Scripts\\python.exe backend\\src\\scripts\\rag_smoke_test.py --query "What are players unhappy about?"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Allow running this file directly while still importing the `src` package.
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.db.vectorial import search_documents
from src.services.llm import generate_rag_response


def parse_args() -> argparse.Namespace:
    """Parse CLI options for a quick end-to-end RAG test."""
    parser = argparse.ArgumentParser(description="Run a quick RAG smoke test")
    parser.add_argument(
        "--query",
        default="What random complaints do players mention?",
        help="Question to test retrieval and generation.",
    )
    parser.add_argument(
        "--collection",
        default="steam_reviews_embeddings",
        help="Chroma collection to query.",
    )
    parser.add_argument(
        "--n-results",
        type=int,
        default=5,
        help="Number of chunks to retrieve from Chroma.",
    )
    parser.add_argument(
        "--model",
        default="mistral",
        help="Ollama model used for generation.",
    )
    return parser.parse_args()


def run_smoke_test(query: str, collection: str, n_results: int, model: str) -> dict[str, Any]:
    """Run retrieval first, then pass context to LLM generation."""
    search = search_documents(query=query, collection_name=collection, n_results=n_results)
    results = search.get("results", [])

    llm = generate_rag_response(query=query, search_results=results, model=model)

    return {
        "search": search,
        "llm": llm,
    }


def main() -> None:
    """Execute quick test and print a concise summary for manual validation."""
    args = parse_args()
    output = run_smoke_test(
        query=args.query,
        collection=args.collection,
        n_results=args.n_results,
        model=args.model,
    )

    search = output["search"]
    llm = output["llm"]

    print(f"SEARCH_STATUS: {search.get('status')}")
    print(f"TOTAL_RESULTS: {search.get('total_results')}")

    for item in search.get("results", [])[:3]:
        print(f"- {item.get('chunk_id')} | dist={item.get('distance')}")

    print(f"LLM_STATUS: {llm.get('status')}")
    answer = llm.get("answer", "")
    print("ANSWER_PREVIEW:")
    print(answer[:1200])


if __name__ == "__main__":
    main()
