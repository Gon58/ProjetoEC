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

    return f"postgresql://{user}:{password}@localhost:{port}/{db}"
    

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
                        parent_log_id INTEGER,
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
            conn.execute(
                text("ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS parent_log_id INTEGER")
            )
    finally:
        engine.dispose()


def log_ingestion_event(
    source: str,
    event_type: str,
    description: str,
    status: str,
    parent_log_id: int | None = None,
    records_count: int | None = None,
    records_skipped: int = 0,
    error_message: str | None = None,
    details: dict[str, Any] | None = None,
) -> int | None:
    postgres_url = _resolve_postgres_url()
    if not postgres_url:
        print("Skipping ingestion log: Postgres connection is not configured.")
        return None

    _ensure_ingestion_logs_table()
    engine = create_engine(postgres_url, echo=False)

    payload = json.dumps(details or {})

    try:
        with engine.begin() as conn:
            inserted_id = conn.execute(
                text(
                    """
                    INSERT INTO ingestion_logs (
                        parent_log_id,
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
                        :parent_log_id,
                        :source,
                        :event_type,
                        :description,
                        :status,
                        :records_count,
                        :records_skipped,
                        :error_message,
                        CAST(:details AS JSONB)
                    )
                    RETURNING id
                    """
                ),
                {
                    "parent_log_id": parent_log_id,
                    "source": source,
                    "event_type": event_type,
                    "description": description,
                    "status": status,
                    "records_count": records_count,
                    "records_skipped": records_skipped,
                    "error_message": error_message,
                    "details": payload,
                },
            ).scalar_one()
            return int(inserted_id)
    except SQLAlchemyError as exc:
        print(f"Failed to persist ingestion log ({source}/{event_type}): {exc}")
        return None
    finally:
        engine.dispose()


def log_child_ingestion_events(
    parent_log_id: int,
    child_events: list[dict[str, Any]],
) -> int:
    """Persist child ingestion logs in batch and link them to a parent log id."""
    if not child_events:
        return 0

    postgres_url = _resolve_postgres_url()
    if not postgres_url:
        print("Skipping child ingestion logs: Postgres connection is not configured.")
        return 0

    _ensure_ingestion_logs_table()
    engine = create_engine(postgres_url, echo=False)

    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO ingestion_logs (
                        parent_log_id,
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
                        :parent_log_id,
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
                [
                    {
                        "parent_log_id": parent_log_id,
                        "source": event.get("source", "postgres_loader"),
                        "event_type": event.get("event_type", "record_loaded"),
                        "description": event.get("description", "Record processed."),
                        "status": event.get("status", "success"),
                        "records_count": event.get("records_count", 1),
                        "records_skipped": event.get("records_skipped", 0),
                        "error_message": event.get("error_message"),
                        "details": json.dumps(event.get("details", {})),
                    }
                    for event in child_events
                ],
            )
    except SQLAlchemyError as exc:
        print(f"Failed to persist child ingestion logs for parent {parent_log_id}: {exc}")
        return 0
    finally:
        engine.dispose()

    return len(child_events)
