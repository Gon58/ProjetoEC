"""Sends predefined questions through the backend /chat pipeline and saves results to JSON.

Usage:
    python eval_llm_questions.py [--n 10] [--mode 3] [--url http://localhost:8080]
                                 [--output-dir ./eval_output]

Modes:
    1 - SQL only   : price and market stats questions (requires a skin name)
    2 - RAG only   : community opinion and sentiment questions
    3 - Both       : all question types including fusion (price + opinion) [default]
"""

import argparse
import csv
import json
import random
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent

DEFAULT_URL = "http://localhost:8080"
DEFAULT_OUTPUT_DIR = _SCRIPT_DIR / "eval_output"
CSV_PATH = _PROJECT_ROOT / "data_pipeline" / "data" / "processed" / "concatenated_kaggle_items.csv"

TEMPLATES = [
    # --- SQL route: exact price / stats questions ---
    {"template": "Olá, podes dizer-me o preço da skin {} por favor?",
     "needs_skin": True, "route": "sql"},
    {"template": "Qual é o preço médio da {}?",
     "needs_skin": True, "route": "sql"},
    {"template": "Qual é o preço mínimo e máximo da {}?",
     "needs_skin": True, "route": "sql"},
    {"template": "Quantas unidades da {} foram vendidas?",
     "needs_skin": True, "route": "sql"},
    {"template": "Quais são as estatísticas de mercado da skin {}?",
     "needs_skin": True, "route": "sql"},
    {"template": "Consegues dizer-me o volume de vendas da {}?",
     "needs_skin": True, "route": "sql"},
    {"template": "Qual é o valor de mercado atual da {}?",
     "needs_skin": True, "route": "sql"},
    {"template": "Quero saber os dados exatos de vendas da skin {}, podes ajudar?",
     "needs_skin": True, "route": "sql"},
    # --- RAG route: community opinion, no specific skin required ---
    {"template": "O que é que a comunidade acha das skins mais populares de CS2 atualmente?",
     "needs_skin": False, "route": "rag"},
    {"template": "Vale a pena investir em skins de CS2 neste momento?",
     "needs_skin": False, "route": "rag"},
    {"template": "O que dizem os jogadores no Reddit sobre o mercado de skins?",
     "needs_skin": False, "route": "rag"},
    {"template": "Quais skins têm as melhores avaliações da comunidade CS2?",
     "needs_skin": False, "route": "rag"},
    # --- Fusion route: price + community opinion combined ---
    {"template": "Tendo em conta o preço, vale a pena comprar a skin {}?",
     "needs_skin": True, "route": "fusion"},
    {"template": "O que diz a comunidade sobre a {} e qual é o seu preço atual?",
     "needs_skin": True, "route": "fusion"},
    {"template": "Devo investir na {}? Tem em conta o preço e a opinião da comunidade.",
     "needs_skin": True, "route": "fusion"},
    {"template": "Com base nos preços e nas opiniões do Reddit, a {} é uma boa compra?",
     "needs_skin": True, "route": "fusion"},
]

def load_skin_names(csv_path: Path) -> list[str]:
    """Reads skin names from the processed Kaggle CSV file.

    Args:
        csv_path: Path to the CSV file containing a 'market_hash_name' column.

    Returns:
        List of non-empty skin name strings.
    """
    skins = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("market_hash_name", "").strip()
            if name:
                skins.append(name)
    return skins


MODE_ROUTES = {
    1: {"sql"},
    2: {"rag"},
    3: {"sql", "rag", "fusion"},
}


def pick_templates(n: int, mode: int) -> list[dict]:
    """Selects n question templates for the given evaluation mode.

    If n exceeds the filtered pool size, templates are repeated to fill the quota.

    Args:
        n: Number of templates to select.
        mode: Evaluation mode (1=SQL, 2=RAG, 3=all routes).

    Returns:
        Randomly sampled list of template dicts.
    """
    pool = [t for t in TEMPLATES if t["route"] in MODE_ROUTES[mode]]
    if n <= len(pool):
        return random.sample(pool, n)
    # Allow repeats when n exceeds filtered pool size
    pool = pool * (n // len(pool) + 1)
    return random.sample(pool, n)


def run_eval(n: int, url: str, output_dir: Path, mode: int) -> None:
    """Runs the evaluation loop and saves results to a timestamped JSON file.

    Sends n questions to the backend /chat endpoint, records each response,
    and writes the full run to eval_output/eval_run_<timestamp>.json.

    Args:
        n: Number of questions to send.
        url: Base URL of the backend (e.g. http://localhost:8080).
        output_dir: Directory where result files are written.
        mode: Evaluation mode controlling which route templates are used.
    """
    print(f"A carregar skins de {CSV_PATH} ...")
    skin_names = load_skin_names(CSV_PATH)
    print(f"  {len(skin_names)} skins carregadas.")

    selected = pick_templates(n, mode)

    skins_needed = sum(1 for t in selected if t["needs_skin"])
    sampled_skins = random.sample(skin_names, min(skins_needed, len(skin_names)))
    skin_iter = iter(sampled_skins)

    results = []
    for i, tmpl in enumerate(selected, start=1):
        skin = next(skin_iter) if tmpl["needs_skin"] else None
        question = tmpl["template"].format(skin) if skin else tmpl["template"]

        print(f"\n[{i}/{n}] ({tmpl['route'].upper()}) {question}")

        entry = {
            "id": i,
            "route": tmpl["route"],
            "template": tmpl["template"],
            "skin": skin,
            "question": question,
        }

        try:
            resp = requests.post(
                f"{url}/chat",
                json={"message": question},
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json()
            entry["answer"] = data.get("answer")
            entry["status"] = data.get("status", "success")
        except requests.exceptions.Timeout:
            entry["answer"] = None
            entry["status"] = "error"
            entry["error"] = "request_timeout"
        except requests.exceptions.ConnectionError:
            entry["answer"] = None
            entry["status"] = "error"
            entry["error"] = "connection_refused"
        except requests.exceptions.HTTPError as e:
            entry["answer"] = None
            entry["status"] = "error"
            entry["error"] = f"http_{e.response.status_code}"
        except Exception as e:
            entry["answer"] = None
            entry["status"] = "error"
            entry["error"] = str(e)

        status_label = entry["status"].upper()
        if entry["status"] == "success":
            preview = (entry["answer"] or "")[:120].replace("\n", " ")
            print(f"  [{status_label}] {preview}...")
        else:
            print(f"  [{status_label}] {entry.get('error')}")

        results.append(entry)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"eval_run_{run_id}.json"

    output = {
        "run_id": run_id,
        "n_questions": n,
        "mode": mode,
        "backend_url": url,
        "template_pool_size": len(TEMPLATES),
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\nConcluído: {success_count}/{n} com sucesso.")
    print(f"Resultados guardados em: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eval LLM questions via backend /chat")
    parser.add_argument("--n", type=int, default=10,
                        help="Number of questions to send (default: 10)")
    parser.add_argument("--mode", type=int, default=3, choices=[1, 2, 3],
                        help="1=SQL, 2=RAG, 3=both (default: 3)")
    parser.add_argument("--url", type=str, default=DEFAULT_URL,
                        help="Backend base URL (default: http://localhost:8080)")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR),
                        help="Directory to save results")
    args = parser.parse_args()

    run_eval(
        n=args.n,
        url=args.url,
        output_dir=Path(args.output_dir),
        mode=args.mode,
    )
