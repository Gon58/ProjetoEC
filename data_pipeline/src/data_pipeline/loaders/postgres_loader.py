import csv
import os

from sqlalchemy import Column, DateTime, Integer, Numeric, String, create_engine, func, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from ..core.utils import to_decimal_2

from dotenv import load_dotenv
load_dotenv()

Base = declarative_base()
SessionLocal = sessionmaker()


class Skin(Base):
    __tablename__ = "skin"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    currency = Column(String)
    min_price = Column(Numeric(10, 2))
    max_price = Column(Numeric(10, 2))
    mean_price = Column(Numeric(10, 2))
    median_price = Column(Numeric(10, 2))
    quantity_sold = Column(Integer)
    source = Column(String)
    last_updated = Column(DateTime, default=func.now())


class SkinPriceHistory(Base):
    __tablename__ = "skin_price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skin_id = Column(Integer, nullable=False)
    skin_name = Column(String, nullable=False)
    recorded_at = Column(DateTime, default=func.now())
    min_price = Column(Numeric(10, 2))
    max_price = Column(Numeric(10, 2))
    mean_price = Column(Numeric(10, 2))
    median_price = Column(Numeric(10, 2))
    quantity_sold = Column(Integer)
    currency = Column(String)
    source = Column(String)


def create_engine_and_session() -> Engine:
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        raise ValueError("POSTGRES_URL must be set in environment variables or .env file")

    engine = create_engine(postgres_url, echo=False)
    SessionLocal.configure(bind=engine)
    return engine


def create_tables(engine: Engine) -> None:
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE skin ADD COLUMN IF NOT EXISTS source VARCHAR"))
        conn.execute(text("ALTER TABLE skin ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))

        # Deduplicate skin table before adding unique constraint
        conn.execute(text("""
            DELETE FROM skin
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM skin
                GROUP BY name, source
            )
        """))

        # Unique index enables ON CONFLICT (name, source) in UPSERT
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS skin_name_source_unique
            ON skin (name, source)
        """))

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
        conn.execute(text("ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS description TEXT"))
        conn.execute(text("ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS parent_log_id INTEGER"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS skin_price_history (
                id SERIAL PRIMARY KEY,
                skin_id INTEGER NOT NULL,
                skin_name VARCHAR NOT NULL,
                recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                min_price NUMERIC(10, 2),
                max_price NUMERIC(10, 2),
                mean_price NUMERIC(10, 2),
                median_price NUMERIC(10, 2),
                quantity_sold INTEGER,
                currency VARCHAR,
                source VARCHAR
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sph_skin_id ON skin_price_history (skin_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_sph_recorded_at ON skin_price_history (recorded_at)
        """))


def parse_quantity(value: str) -> int:
    if not value:
        return 0

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def build_skin_from_row(row: dict) -> Skin:
    return Skin(
        name=row.get("market_hash_name"),
        currency=row.get("currency"),
        min_price=to_decimal_2(row.get("min_price")),
        max_price=to_decimal_2(row.get("max_price")),
        mean_price=to_decimal_2(row.get("mean_price")),
        median_price=to_decimal_2(row.get("median_price")),
        quantity_sold=parse_quantity(row.get("quantity_sold")),
        source=row.get("source"),
    )


_UPSERT_SKIN = text("""
    INSERT INTO skin
        (name, currency, min_price, max_price, mean_price, median_price, quantity_sold, source, last_updated)
    VALUES
        (:name, :currency, :min_price, :max_price, :mean_price, :median_price, :quantity_sold, :source, CURRENT_TIMESTAMP)
    ON CONFLICT (name, source) DO UPDATE SET
        min_price    = EXCLUDED.min_price,
        max_price    = EXCLUDED.max_price,
        mean_price   = EXCLUDED.mean_price,
        median_price = EXCLUDED.median_price,
        quantity_sold = EXCLUDED.quantity_sold,
        last_updated = CURRENT_TIMESTAMP
    RETURNING id, name, min_price, max_price, mean_price, median_price, quantity_sold, currency
""")

_INSERT_HISTORY = text("""
    INSERT INTO skin_price_history
        (skin_id, skin_name, min_price, max_price, mean_price, median_price, quantity_sold, currency, source)
    VALUES
        (:skin_id, :skin_name, :min_price, :max_price, :mean_price, :median_price, :quantity_sold, :currency, :source)
""")


def load_from_csv_to_db(csv_path: str, session: Session) -> int:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    count = 0

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            params = {
                "name": row.get("market_hash_name"),
                "currency": row.get("currency"),
                "min_price": to_decimal_2(row.get("min_price")),
                "max_price": to_decimal_2(row.get("max_price")),
                "mean_price": to_decimal_2(row.get("mean_price")),
                "median_price": to_decimal_2(row.get("median_price")),
                "quantity_sold": parse_quantity(row.get("quantity_sold")),
                "source": row.get("source"),
            }

            result = session.execute(_UPSERT_SKIN, params)
            skin_row = result.one()

            session.execute(_INSERT_HISTORY, {
                "skin_id": skin_row.id,
                "skin_name": skin_row.name,
                "min_price": skin_row.min_price,
                "max_price": skin_row.max_price,
                "mean_price": skin_row.mean_price,
                "median_price": skin_row.median_price,
                "quantity_sold": skin_row.quantity_sold,
                "currency": skin_row.currency,
                "source": params["source"],
            })

            count += 1
            if count % 1000 == 0:
                session.commit()

        session.commit()

    return count