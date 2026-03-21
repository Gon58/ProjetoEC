from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

from ..core.config import POSTGRES_URL


def _get_engine():
    """Creates engine from POSTGRES_URL."""
    if not POSTGRES_URL:
        raise ValueError("POSTGRES_URL is not configured")
    return create_engine(POSTGRES_URL, echo=False)


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
