import csv
import os

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import Column, Integer, Numeric, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from utils import decode_base64, to_decimal_2

load_dotenv()

POSTGRES_URL = os.getenv("POSTGRES_URL")

if not POSTGRES_URL:
    raise ValueError("POSTGRES_URL must be set in environment variables or .env file")


Base = declarative_base()
SessionLocal = sessionmaker()

SKINPORT_URL = "https://api.skinport.com/v1/items"
HEADERS = {"Accept-Encoding": "br", "User-Agent": "PythonSkinPortClient/1.0"}


class Skin(Base):
    __tablename__ = "skin"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    currency = Column(String)
    min_price = Column(Numeric(10, 2))
    max_price = Column(Numeric(10, 2))
    mean_price = Column(Numeric(10, 2))
    median_price = Column(Numeric(10, 2))
    quantity_sold = Column(Integer)

    def __repr__(self) -> str:
        return (
            f"Skin(id={self.id}, "
            f"name='{self.name}', "
            f"currency='{self.currency}', "
            f"min_price='{self.min_price}', "
            f"max_price='{self.max_price}')"
        )


def create_engine_and_session():
    """Cria engine e sessão."""
    engine = create_engine(POSTGRES_URL, echo=False)
    SessionLocal.configure(bind=engine)
    return engine


def create_tables(engine):
    """Cria as tabelas."""
    Base.metadata.create_all(engine)


def fetch_skinport_data(app_id=730, currency="USD", tradable=True):
    print("Fetching data from Skinport API...")
    params = {"app_id": app_id, "currency": currency, "tradable": 1 if tradable else 0}
    res = requests.get(SKINPORT_URL, params=params, headers=HEADERS)
    if res.status_code != 200:
        print(f"Error fetching Skinport: {res.status_code}")
        return []

    items = res.json()
    formatted_items = []
    for item in items:
        formatted_items.append(
            {
                "market_hash_name": item.get("market_hash_name"),
                "currency": item.get("currency"),
                "min_price": item.get("min_price"),
                "max_price": item.get("max_price"),
                "mean_price": item.get("mean_price"),
                "median_price": item.get("median_price"),
                "quantity_sold": item.get("quantity"),
            }
        )
    return formatted_items


def get_kaggle_processed_data(kaggle_dir):
    index_file = os.path.join(kaggle_dir, "item_index.csv")
    items_dir = os.path.join(kaggle_dir, "items")

    if not os.path.exists(index_file):
        print(f"Index file not found: {index_file}")
        return []

    df_index = pd.read_csv(index_file)
    results = []
    total_items = len(df_index)

    print(f"Processing {total_items} Kaggle items...")
    for i, row in df_index.iterrows():
        base64_name = row["item_hash_name_base64"]
        file_name = row["file_name"]

        market_hash_name = decode_base64(base64_name)
        item_path = os.path.join(items_dir, file_name)

        if os.path.exists(item_path):
            try:
                df_item = pd.read_csv(item_path)
                if df_item.empty:
                    continue

                prices = df_item["price_dollar"]
                sells = df_item["sells"]

                results.append(
                    {
                        "market_hash_name": market_hash_name,
                        "currency": "USD",
                        "min_price": prices.min(),
                        "max_price": prices.max(),
                        "mean_price": prices.mean(),
                        "median_price": prices.median(),
                        "quantity_sold": int(sells.sum()),
                    }
                )
            except Exception:
                pass

        if (i + 1) % 5000 == 0:
            print(f"Processed {i + 1}/{total_items} Kaggle items...")

    return results


def load_from_csv_to_db(csv_path: str, session: Session) -> None:
    print(f"Loading data from {csv_path} to database...")
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        for row in reader:
            product = Skin(
                name=row["market_hash_name"],
                currency=row["currency"],
                min_price=to_decimal_2(row["min_price"]),
                max_price=to_decimal_2(row["max_price"]),
                mean_price=to_decimal_2(row["mean_price"]),
                median_price=to_decimal_2(row["median_price"]),
                quantity_sold=int(float(row["quantity_sold"])) if row["quantity_sold"] else 0,
            )
            session.add(product)
            count += 1
            if count % 1000 == 0:
                session.commit()
        session.commit()
    print(f"Successfully loaded {count} items.")


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    kaggle_dir = os.path.join(base_dir, "kaggle_dataset")
    output_csv = os.path.join(base_dir, "combined_data.csv")

    skinport_items = fetch_skinport_data()
    kaggle_items = get_kaggle_processed_data(kaggle_dir)

    print("Combining datasets...")
    df_skinport = pd.DataFrame(skinport_items)
    df_kaggle = pd.DataFrame(kaggle_items)

    df_combined = pd.concat([df_skinport, df_kaggle], ignore_index=True)
    df_combined.to_csv(output_csv, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"Combined data saved to {output_csv}")

    engine = create_engine_and_session()
    create_tables(engine)
    session = SessionLocal()

    try:
        load_from_csv_to_db(output_csv, session)
    except Exception as e:
        print(f"Error loading to DB: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
