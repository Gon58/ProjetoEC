from sqlalchemy.orm import sessionmaker
from data_pipeline.loaders.postgres_loader import (
    create_engine_and_session,
    create_tables,
    load_from_csv_to_db,
)


def test_postgres_load(tmp_path):
    # criar CSV pequeno
    csv_file = tmp_path / "test.csv"

    csv_file.write_text(
        "market_hash_name,currency,min_price,max_price,mean_price,median_price,quantity_sold\n"
        "AK-47,USD,10,20,15,14,100\n"
    )

    engine = create_engine_and_session()
    create_tables(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    count = load_from_csv_to_db(str(csv_file), session)

    assert count == 1