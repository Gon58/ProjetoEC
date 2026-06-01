"""
Loads skin_price_history.csv into the skin_price_history PostgreSQL table.

Use this after a full DB reset (docker compose down -v) instead of regenerating
the random walk from scratch.

    python data_pipeline/scripts/load_history_from_csv.py

The script:
  1. Reads data/processed/skin_price_history.csv
  2. Looks up skin_id for each (skin_name, source) pair from the skin table
  3. Inserts into skin_price_history (skips rows where skin_id not found)
"""

import csv
import os
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

POSTGRES_URL = os.getenv("POSTGRES_URL", "").replace("postgresql+psycopg://", "postgresql://")
CSV_FILE = Path(__file__).resolve().parents[1] / "data" / "processed" / "skin_price_history.csv"
BATCH_SIZE = 500


def main() -> None:
    if not POSTGRES_URL:
        raise SystemExit("POSTGRES_URL is not set in .env")

    if not CSV_FILE.exists():
        raise SystemExit(
            f"CSV not found: {CSV_FILE}\n"
            "Run generate_steam_history.py first to create it."
        )

    print(f"Reading {CSV_FILE}…")

    with psycopg.connect(POSTGRES_URL) as conn:
        # Build name+source → skin_id lookup cache
        print("Building skin ID lookup cache…")
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, source FROM skin")
            skin_map: dict[tuple[str, str], int] = {
                (name, source): sid for sid, name, source in cur.fetchall()
            }
        print(f"  {len(skin_map):,} skins loaded into cache.")

        # Check existing history
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM skin_price_history")
            existing = cur.fetchone()[0]

        if existing > 0:
            answer = input(
                f"skin_price_history already has {existing:,} rows. "
                "Delete and reload? [y/N] "
            ).strip().lower()
            if answer != "y":
                print("Aborted.")
                return
            with conn.cursor() as cur:
                cur.execute("DELETE FROM skin_price_history")
            conn.commit()
            print("Existing history deleted.")

        # Load CSV
        total = 0
        skipped = 0
        batch: list[tuple] = []

        with CSV_FILE.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row["skin_name"]
                source = row["source"]
                skin_id = skin_map.get((name, source))
                if skin_id is None:
                    skipped += 1
                    continue

                batch.append((
                    skin_id,
                    name,
                    datetime.fromisoformat(row["recorded_at"]),
                    float(row["min_price"]),
                    float(row["max_price"]),
                    float(row["mean_price"]),
                    float(row["median_price"]),
                    int(row["quantity_sold"]) if row["quantity_sold"] else 0,
                    row["currency"],
                    source,
                ))

                if len(batch) >= BATCH_SIZE:
                    with conn.cursor() as cur:
                        cur.executemany(
                            """
                            INSERT INTO skin_price_history
                                (skin_id, skin_name, recorded_at, min_price, max_price,
                                 mean_price, median_price, quantity_sold, currency, source)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            batch,
                        )
                    conn.commit()
                    total += len(batch)
                    batch.clear()
                    if total % 10000 == 0:
                        print(f"  {total:,} rows inserted…")

        if batch:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO skin_price_history
                        (skin_id, skin_name, recorded_at, min_price, max_price,
                         mean_price, median_price, quantity_sold, currency, source)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    batch,
                )
            conn.commit()
            total += len(batch)

    print(f"\nDone. {total:,} rows inserted. {skipped:,} rows skipped (skin not in DB).")


if __name__ == "__main__":
    main()
