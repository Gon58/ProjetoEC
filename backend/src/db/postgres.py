import os
from typing import Any

from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError


def _get_engine():
    """Cria engine a partir da variável POSTGRES_URL."""
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        postgres_url = URL.create(
            drivername="postgresql+psycopg",
            username=os.getenv("POSTGRES_USER", "ec_project"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "ec_project"),
        )
    return create_engine(postgres_url, echo=False)


def fetch_skinport_skins(limit: int = 100) -> list[dict[str, Any]]:
    """Fetch skin rows from PostgreSQL restricted to Skinport records."""
    query = text("""
        SELECT name, currency, min_price, max_price, mean_price, median_price, quantity_sold, source
        FROM skin
        WHERE source = :source
        ORDER BY mean_price DESC
        LIMIT :limit
    """)

    with _get_engine().connect() as conn:
        try:
            rows = conn.execute(query, {"source": "skinport", "limit": limit}).mappings().all()
        except (OperationalError, ProgrammingError):
            return []

    return [dict(row) for row in rows]


def fetch_skinport_skin_by_name(name: str) -> dict[str, Any] | None:
    """Fetch one Skinport skin by exact name from PostgreSQL."""
    query = text("""
        SELECT name, currency, min_price, max_price, mean_price, median_price, quantity_sold, source
        FROM skin
        WHERE source = :source AND name = :name
        LIMIT 1
    """)

    with _get_engine().connect() as conn:
        try:
            row = (
                conn.execute(query, {"source": "skinport", "name": name})
                .mappings()
                .first()
            )
        except (OperationalError, ProgrammingError):
            return None

    if not row:
        return None

    return dict(row)
