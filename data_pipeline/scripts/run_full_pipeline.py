from pathlib import Path
import subprocess
import sys


def run_step(script_path: Path, label: str) -> None:
    print(f"\n=== {label} ===")
    result = subprocess.run([sys.executable, str(script_path)], check=False)

    if result.returncode != 0:
        raise SystemExit(f"Step failed: {label} ({script_path.name})")


def main():
    base_dir = Path(__file__).resolve().parents[1]
    scripts_dir = base_dir / "scripts"

    steps = [
        (scripts_dir / "run_kaggle_processing.py", "Process Kaggle dataset"),
        (scripts_dir / "run_skinport_ingestion.py", "Fetch and normalize Skinport data"),
        (scripts_dir / "run_merge.py", "Merge Kaggle and Skinport datasets"),
        (scripts_dir / "run_load_postgres.py", "Load merged data into PostgreSQL"),
    ]

    for script, label in steps:
        run_step(script, label)

    print("\nFull pipeline completed successfully.")


if __name__ == "__main__":
    main()