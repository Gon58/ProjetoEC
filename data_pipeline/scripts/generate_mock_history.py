"""
Generates 30 days of simulated price history for the top skins.

Run this once after the pipeline has loaded skin data:
    python data_pipeline/scripts/generate_mock_history.py

The script is idempotent: it skips generation if history already exists.
To regenerate: DELETE FROM skin_price_history; then run again.
"""
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

POSTGRES_URL = os.getenv("POSTGRES_URL", "").replace("postgresql+psycopg://", "postgresql://")
DAYS = 30
MAX_SKINS = 200  # Generate history for top 200 skins by price


def _random_walk(base: float, days: int) -> list[float]:
    """Returns a list of `days` prices ending at `base`, oldest first."""
    prices = [base]
    for _ in range(days - 1):
        shock = random.gauss(0, 0.025)
        if random.random() < 0.05:
            shock += random.gauss(0, 0.06)
        prices.append(max(prices[-1] / (1 + shock), 0.01))
    prices.reverse()
    return prices


def main() -> None:
    if not POSTGRES_URL:
        raise SystemExit("POSTGRES_URL is not set in .env")

    with psycopg.connect(POSTGRES_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM skin_price_history")
            if cur.fetchone()[0] > 0:
                print("History already exists. Delete from skin_price_history to regenerate.")
                return

            cur.execute("""
                SELECT id, name, min_price, max_price, mean_price,
                       median_price, quantity_sold, currency, source
                FROM skin
                WHERE mean_price > 0
                ORDER BY mean_price DESC
                LIMIT %s
            """, (MAX_SKINS,))
            skins = cur.fetchall()

        if not skins:
            print("No skins found. Run the ingestion pipeline first.")
            return

        print(f"Generating {DAYS} days of mock history for {len(skins)} skins...")

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        total = 0

        with conn.cursor() as cur:
            for (skin_id, name, min_p, max_p, mean_p,
                 median_p, qty, currency, source) in skins:
                mean_p = float(mean_p or 1.0)
                min_p = float(min_p or mean_p * 0.70)
                max_p = float(max_p or mean_p * 1.30)
                median_p = float(median_p or mean_p)

                mean_series = _random_walk(mean_p, DAYS)
                min_series = _random_walk(min_p, DAYS)
                max_series = _random_walk(max_p, DAYS)

                for day_offset in range(DAYS):
                    recorded_at = today - timedelta(days=DAYS - day_offset - 1)
                    mp = round(mean_series[day_offset], 2)
                    minp = round(min(min_series[day_offset], mp * 0.95), 2)
                    maxp = round(max(max_series[day_offset], mp * 1.05), 2)
                    medp = round(median_p * (mp / mean_p), 2)

                    cur.execute("""
                        INSERT INTO skin_price_history
                            (skin_id, skin_name, recorded_at, min_price, max_price,
                             mean_price, median_price, quantity_sold, currency, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (skin_id, name, recorded_at, minp, maxp, mp, medp, qty, currency, source))
                    total += 1

                if total % 2000 == 0:
                    conn.commit()
                    print(f"  {total} records inserted…")

            conn.commit()

        print(f"Done. {total} mock history records created for {len(skins)} skins.")


if __name__ == "__main__":
    main()
