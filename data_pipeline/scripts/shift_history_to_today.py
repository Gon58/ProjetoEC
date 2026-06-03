"""
Shifts the price-history mock data so the most recent record lands on today.

The mock data was generated with fixed dates (newest = 2026-05-16). As real time
moves on, a NOW()-based window (last 7/14 days) stops finding rows. Running this
re-dates the whole series forward so the newest record == today's date, preserving
the relative spacing between every record.

Updates BOTH:
  1. data/processed/skin_price_history.csv  (source of truth for reloads)
  2. the skin_price_history table in PostgreSQL (live data)

Each store is shifted by its own (today - max_date) delta, so the script is
idempotent — running it again when the data is already current is a no-op.

    python data_pipeline/scripts/shift_history_to_today.py
"""

import csv
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

POSTGRES_URL = os.getenv("POSTGRES_URL", "").replace("postgresql+psycopg://", "postgresql://")
CSV_FILE = Path(__file__).resolve().parents[1] / "data" / "processed" / "skin_price_history.csv"


def _parse(value: str) -> datetime:
    """Parse a recorded_at cell, which may be a date or full ISO timestamp."""
    return datetime.fromisoformat(value)


def shift_csv(today: date) -> int:
    """Rewrite the CSV with every recorded_at shifted so the newest == today."""
    if not CSV_FILE.exists():
        print(f"CSV not found, skipping: {CSV_FILE}")
        return 0

    with CSV_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    if not rows:
        print("CSV has no rows, skipping.")
        return 0

    max_dt = max(_parse(r["recorded_at"]) for r in rows)
    delta = today - max_dt.date()
    if delta.days == 0:
        print("CSV already current (newest record is today). No change.")
        return 0

    for r in rows:
        original = _parse(r["recorded_at"])
        shifted = original + timedelta(days=delta.days)
        # Keep the original formatting style (date-only vs full timestamp).
        r["recorded_at"] = (
            shifted.date().isoformat() if len(r["recorded_at"]) <= 10 else shifted.isoformat()
        )

    with CSV_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV shifted by {delta.days} days ({max_dt.date()} -> {today}). {len(rows):,} rows.")
    return delta.days


def shift_db(today: date) -> None:
    """Shift recorded_at in PostgreSQL so the newest record == today."""
    if not POSTGRES_URL:
        print("POSTGRES_URL not set, skipping DB shift.")
        return

    with psycopg.connect(POSTGRES_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(recorded_at)::date FROM skin_price_history")
            row = cur.fetchone()
            if not row or row[0] is None:
                print("skin_price_history is empty, skipping DB shift.")
                return
            db_max = row[0]
            delta_days = (today - db_max).days
            if delta_days == 0:
                print("DB already current (newest record is today). No change.")
                return

            cur.execute(
                "UPDATE skin_price_history "
                "SET recorded_at = recorded_at + (%s || ' days')::INTERVAL",
                (delta_days,),
            )
            conn.commit()
            print(f"DB shifted by {delta_days} days ({db_max} -> {today}). {cur.rowcount:,} rows.")


def main() -> None:
    today = date.today()
    print(f"Target date (today): {today}\n")
    shift_csv(today)
    shift_db(today)
    print("\nDone.")


if __name__ == "__main__":
    main()
