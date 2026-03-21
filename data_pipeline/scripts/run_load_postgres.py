from pathlib import Path
from data_pipeline.loaders.postgres_loader import (
    create_engine_and_session,
    create_tables,
    load_from_csv_to_db,
    SessionLocal,
)

base_dir = Path(__file__).resolve().parents[1]


def main():
    base_dir = Path(__file__).resolve().parents[1]
    csv_file = base_dir / "data" / "processed" / "combined_data.csv"

    engine = create_engine_and_session()
    create_tables(engine)
    session = SessionLocal()

    try:
        count = load_from_csv_to_db(str(csv_file), session)
        print(f"Loaded {count} rows into PostgreSQL")
    except Exception as e:
        session.rollback()
        print(f"Error loading data: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
