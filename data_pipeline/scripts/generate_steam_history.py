"""
Generates 30 days of simulated price history for ALL Steam Market skins.

Saves results to:
  data/processed/skin_price_history.csv   ← portable, DB-independent
  skin_price_history table in PostgreSQL  ← ready to use immediately

Run after loading skins into PostgreSQL:
    python data_pipeline/scripts/generate_steam_history.py

The script is idempotent for steam_market: if steam_market rows already exist
in skin_price_history it skips generation (pass --force to regenerate).
"""

import argparse
import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

POSTGRES_URL = os.getenv("POSTGRES_URL", "").replace("postgresql+psycopg://", "postgresql://")
DAYS = 30
SOURCE = "steam_market"
OUTPUT_CSV = Path(__file__).resolve().parents[1] / "data" / "processed" / "skin_price_history.csv"
BATCH_SIZE = 500


def _random_walk(base: float, days: int) -> list[float]:
    prices = [base]
    for _ in range(days - 1):
        shock = random.gauss(0, 0.025)
        if random.random() < 0.05:
            shock += random.gauss(0, 0.06)
        prices.append(max(prices[-1] / (1 + shock), 0.01))
    prices.reverse()
    return prices


def main(force: bool = False) -> None:
    if not POSTGRES_URL:
        raise SystemExit("POSTGRES_URL is not set in .env")

    with psycopg.connect(POSTGRES_URL) as conn:
        # Check if steam history already exists
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM skin_price_history WHERE source = %s",
                (SOURCE,),
            )
            existing = cur.fetchone()[0]

        if existing > 0 and not force:
            print(
                f"Steam history already exists ({existing} rows). "
                "Use --force to regenerate."
            )
            return

        if existing > 0 and force:
            print(f"Deleting {existing} existing steam_market history rows…")
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM skin_price_history WHERE source = %s", (SOURCE,)
                )
            conn.commit()

        # Fetch all steam skins
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, min_price, max_price, mean_price,
                       median_price, quantity_sold, currency
                FROM skin
                WHERE source = %s AND mean_price > 0
                ORDER BY mean_price DESC
                """,
                (SOURCE,),
            )
            skins = cur.fetchall()

    if not skins:
        print(f"No skins with source='{SOURCE}' found. Run the pipeline first.")
        return

    print(f"Generating {DAYS} days of history for {len(skins)} {SOURCE} skins…")
    print(f"Total rows to generate: {len(skins) * DAYS:,}")

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    dates = [today - timedelta(days=DAYS - i - 1) for i in range(DAYS)]

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    total_written = 0

    with (
        psycopg.connect(POSTGRES_URL) as conn,
        OUTPUT_CSV.open("w", newline="", encoding="utf-8") as csvfile,
    ):
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "skin_name", "source", "recorded_at",
                "min_price", "max_price", "mean_price",
                "median_price", "quantity_sold", "currency",
            ]
        )

        batch_db: list[tuple] = []
        batch_csv: list[list] = []

        for skin_id, name, min_p, max_p, mean_p, median_p, qty, currency in skins:
            mean_p = float(mean_p or 1.0)
            min_p = float(min_p or mean_p * 0.70)
            max_p = float(max_p or mean_p * 1.30)
            median_p = float(median_p or mean_p)

            mean_series = _random_walk(mean_p, DAYS)
            min_series = _random_walk(min_p, DAYS)
            max_series = _random_walk(max_p, DAYS)

            for i, recorded_at in enumerate(dates):
                mp = round(mean_series[i], 4)
                minp = round(min(min_series[i], mp * 0.95), 4)
                maxp = round(max(max_series[i], mp * 1.05), 4)
                medp = round(median_p * (mp / mean_p), 4)

                batch_db.append(
                    (skin_id, name, recorded_at, minp, maxp, mp, medp, qty, currency, SOURCE)
                )
                batch_csv.append(
                    [name, SOURCE, recorded_at.date().isoformat(), minp, maxp, mp, medp, qty, currency]
                )

            if len(batch_db) >= BATCH_SIZE:
                with conn.cursor() as cur:
                    cur.executemany(
                        """
                        INSERT INTO skin_price_history
                            (skin_id, skin_name, recorded_at, min_price, max_price,
                             mean_price, median_price, quantity_sold, currency, source)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        batch_db,
                    )
                conn.commit()
                writer.writerows(batch_csv)
                total_written += len(batch_db)
                print(f"  {total_written:,} rows inserted…")
                batch_db.clear()
                batch_csv.clear()

        # Final flush
        if batch_db:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO skin_price_history
                        (skin_id, skin_name, recorded_at, min_price, max_price,
                         mean_price, median_price, quantity_sold, currency, source)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    batch_db,
                )
            conn.commit()
            writer.writerows(batch_csv)
            total_written += len(batch_db)

    print("\nDone.")
    print(f"  {total_written:,} history rows inserted into PostgreSQL.")
    print(f"  CSV saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Delete existing steam history and regenerate")
    args = parser.parse_args()
    main(force=args.force)
