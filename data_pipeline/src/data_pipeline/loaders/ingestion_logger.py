import json
import os
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()


def _resolve_postgres_url() -> str | None:
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        return postgres_url

    port = os.getenv("POSTGRES_PORT") or "5433"
    db = os.getenv("POSTGRES_DB")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not all([db, user, password]):
        return None

    return f"postgresql://{user}:{password}@127.0.0.1:{port}/{db}"
    

def _ensure_ingestion_logs_table() -> None:
    postgres_url = _resolve_postgres_url()
    if not postgres_url:
        return

    engine = create_engine(postgres_url, echo=False)

    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS ingestion_logs (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        source VARCHAR(50) NOT NULL,
                        event_type VARCHAR(50) NOT NULL,
                        description TEXT,
                        status VARCHAR(20) NOT NULL,
                        records_count INTEGER,
                        records_skipped INTEGER NOT NULL DEFAULT 0,
                        error_message TEXT,
                        details JSONB
                    )
                    """
                )
            )
            conn.execute(
                text("ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS description TEXT")
            )
    finally:
        engine.dispose()


def log_ingestion_event(
    source: str,
    event_type: str,
    description: str,
    status: str,
    records_count: int | None = None,
    records_skipped: int = 0,
    error_message: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    postgres_url = _resolve_postgres_url()
    if not postgres_url:
        print("Skipping ingestion log: Postgres connection is not configured.")
        return

    _ensure_ingestion_logs_table()
    engine = create_engine(postgres_url, echo=False)

    payload = json.dumps(details or {})

    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO ingestion_logs (
                        source,
                        event_type,
                        description,
                        status,
                        records_count,
                        records_skipped,
                        error_message,
                        details
                    )
                    VALUES (
                        :source,
                        :event_type,
                        :description,
                        :status,
                        :records_count,
                        :records_skipped,
                        :error_message,
                        CAST(:details AS JSONB)
                    )
                    """
                ),
                {
                    "source": source,
                    "event_type": event_type,
                    "description": description,
                    "status": status,
                    "records_count": records_count,
                    "records_skipped": records_skipped,
                    "error_message": error_message,
                    "details": payload,
                },
            )
    except SQLAlchemyError as exc:
        print(f"Failed to persist ingestion log ({source}/{event_type}): {exc}")
    finally:
        engine.dispose()
