from pathlib import Path
from data_pipeline.loaders.postgres_loader import (
    create_engine_and_session,
    create_tables,
    load_from_csv_to_db,
    SessionLocal,
)
from data_pipeline.loaders.ingestion_logger import log_ingestion_event

base_dir = Path(__file__).resolve().parents[1]


def main():
    base_dir = Path(__file__).resolve().parents[1]
    csv_file = base_dir / "data" / "processed" / "combined_data.csv"

    engine = create_engine_and_session()
    create_tables(engine)
    session = SessionLocal()

    try:
        count = load_from_csv_to_db(str(csv_file), session)
        log_ingestion_event(
            source="postgres_loader",
            event_type="ingestion_run",
            description=f"Loaded {count} merged records from CSV into PostgreSQL.",
            status="success",
            records_count=count,
            details={"input_file": str(csv_file)},
        )
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
