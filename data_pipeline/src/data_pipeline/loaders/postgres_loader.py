import csv
import os

from sqlalchemy import Column, Integer, Numeric, String, create_engine, text
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


def load_from_csv_to_db(csv_path: str, session: Session) -> int:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    count = 0

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            product = build_skin_from_row(row)
            session.add(product)
            count += 1

            if count % 1000 == 0:
                session.commit()

        session.commit()

    return count