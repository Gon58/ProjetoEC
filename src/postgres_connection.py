from sqlalchemy import create_engine, Column, Integer, String, Numeric
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os
import csv
from decimal import Decimal, ROUND_HALF_UP

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://ec_project:ec_project_pass@localhost:5433/ec_project")

Base = declarative_base()
SessionLocal = sessionmaker()

class Skin(Base):
    __tablename__ = "skin"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    currency = Column(String)
    min_price = Column(Numeric(7,2))
    max_price = Column(Numeric(7,2))
    mean_price = Column(Numeric(7,2))
    median_price = Column(Numeric(7,2))
    quantity_sold = Column(Integer)

    def __repr__(self) -> str:
        return f"Skin(id={self.id}, name='{self.name}, currency='{self.currency}', min_price='{self.min_price}', max_price='{self.max_price}')"

def create_engine_and_session():
    """Cria engine e sessão."""
    engine = create_engine(POSTGRES_URL, echo=False)
    SessionLocal.configure(bind=engine)
    return engine

def create_tables(engine):
    """Cria as tabelas."""
    Base.metadata.create_all(engine)

def to_decimal_2(value: str) -> Decimal:
    """
    Converte string numérica para Decimal com 2 casas decimais.
    """
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def load_products_from_csv(csv_path: str, session: Session) -> None:
    """
    Lê um CSV, transforma os valores decimais em valores com 2 casas decimais
    e insere os dados na base de dados.
    """

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            product = Skin(
                name=row["market_hash_name"],
                currency=row["currency"],
                min_price=to_decimal_2(row["min_price"]),
                max_price=to_decimal_2(row["max_price"]),
                mean_price=to_decimal_2(row["mean_price"]),
                median_price=to_decimal_2(row["median_price"]),
                quantity_sold=int(row["quantity_sold"]),
            )

            session.add(product)

        session.commit()

def print_tables_content(session: Session):
    """Dá print do conteúdo das tabelas."""

    skins = session.query(Skin).all()

    print("\n=== SKINS ===")
    for skin in skins:
        print(skin)

    session.close()

def main() -> None:
    engine = create_engine_and_session()
    create_tables(engine)
    session = SessionLocal()
    load_products_from_csv("../data_scripts/kaggle_dataset/concatenated_kaggle_items.csv", session)
    print_tables_content(session)



if __name__ == "__main__":
    main()