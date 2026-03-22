import csv
from pathlib import Path
from data_pipeline.loaders.postgres_loader import (
    create_engine_and_session,
    create_tables,
    load_from_csv_to_db,
    SessionLocal,
)
from data_pipeline.loaders.ingestion_logger import log_child_ingestion_events, log_ingestion_event

base_dir = Path(__file__).resolve().parents[1]


def emit_child_logs_for_csv(csv_file: Path, parent_log_id: int, batch_size: int = 1000) -> int:
    total_logged = 0
    batch: list[dict] = []

    with csv_file.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)

        for index, row in enumerate(reader, start=1):
            item_name = row.get("market_hash_name") or "unknown_item"
            item_source = row.get("source") or "unknown_source"

            batch.append(
                {
                    "source": "postgres_loader",
                    "event_type": "record_loaded",
                    "description": f"Loaded record #{index}: {item_name} ({item_source}).",
                    "status": "success",
                    "records_count": 1,
                    "details": {
                        "record_index": index,
                        "market_hash_name": item_name,
                        "item_source": item_source,
                    },
                }
            )

            if len(batch) >= batch_size:
                total_logged += log_child_ingestion_events(parent_log_id=parent_log_id, child_events=batch)
                batch = []

    if batch:
        total_logged += log_child_ingestion_events(parent_log_id=parent_log_id, child_events=batch)

    return total_logged


def main():
    base_dir = Path(__file__).resolve().parents[1]
    csv_file = base_dir / "data" / "processed" / "combined_data.csv"

    engine = create_engine_and_session()
    create_tables(engine)
    session = SessionLocal()

    try:
        count = load_from_csv_to_db(str(csv_file), session)
        parent_log_id = log_ingestion_event(
            source="postgres_loader",
            event_type="ingestion_run",
            description=f"Loaded {count} merged records from CSV into PostgreSQL.",
            status="success",
            records_count=count,
            details={"input_file": str(csv_file)},
        )
        if parent_log_id is not None:
            child_count = emit_child_logs_for_csv(csv_file=csv_file, parent_log_id=parent_log_id)
            print(f"Created {child_count} child logs linked to parent log {parent_log_id}")
        print(f"Loaded {count} rows into PostgreSQL")
    except Exception as e:
        session.rollback()
        log_ingestion_event(
            source="postgres_loader",
            event_type="ingestion_run",
            description="PostgreSQL load failed while inserting merged CSV records.",
            status="error",
            records_count=0,
            error_message=str(e),
            details={"input_file": str(csv_file)},
        )
        print(f"Error loading data: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
