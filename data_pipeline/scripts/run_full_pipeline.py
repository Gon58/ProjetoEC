from pathlib import Path
import os
import subprocess
import sys


def run_step(script_path: Path, label: str) -> None:
    print(f"\n=== {label} ===")
    base_dir = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    src_path = str(base_dir / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else src_path
    result = subprocess.run([sys.executable, str(script_path)], check=False, cwd=str(base_dir), env=env)

    if result.returncode != 0:
        raise SystemExit(f"Step failed: {label} ({script_path.name})")


def main():
    base_dir = Path(__file__).resolve().parents[1]
    scripts_dir = base_dir / "scripts"
    run_reddit_ingestion = os.getenv("RUN_REDDIT_INGESTION", "false").strip().lower() in {"1", "true", "yes", "on"}
    run_reddit_vector_indexing = os.getenv("RUN_REDDIT_VECTOR_INDEXING", "false").strip().lower() in {"1", "true", "yes", "on"}

    steps = [
        (scripts_dir / "run_kaggle_processing.py",  "Process Kaggle dataset"),
        (scripts_dir / "run_skinport_ingestion.py", "Fetch and normalize Skinport data"),
        (scripts_dir / "run_steam_market.py",       "Scrape Steam Market"),
        (scripts_dir / "run_merge.py",              "Merge all datasets"),
        (scripts_dir / "run_load_postgres.py",      "Load merged data into PostgreSQL"),
    ]

    if run_reddit_ingestion:
        steps.append(
            (scripts_dir / "run_reddit_ingestion.py", "Fetch Reddit posts into MongoDB")
        )

    if run_reddit_vector_indexing:
        steps.append(
            (scripts_dir / "run_reddit_vector_indexing.py", "Index Reddit discussions into ChromaDB")
        )

    for script, label in steps:
        run_step(script, label)

    print("\nFull pipeline completed successfully.")


if __name__ == "__main__":
    main()