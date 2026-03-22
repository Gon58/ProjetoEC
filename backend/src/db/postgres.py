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


def fetch_parent_ingestion_logs(page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    """Fetch paginated parent logs (rows where parent_log_id is NULL)."""
    offset = (page - 1) * page_size

    query = text(
        """
        SELECT
            l.id,
            l.timestamp,
            l.source,
            COALESCE(l.details ->> 'database', 'postgres') AS database,
            COALESCE(l.description, '') AS description,
            COALESCE(c.children_count, 0) AS children_count
        FROM ingestion_logs l
        LEFT JOIN (
            SELECT parent_log_id, COUNT(*) AS children_count
            FROM ingestion_logs
            WHERE parent_log_id IS NOT NULL
            GROUP BY parent_log_id
        ) c ON c.parent_log_id = l.id
        WHERE l.parent_log_id IS NULL
        ORDER BY l.timestamp DESC, l.id DESC
        LIMIT :limit OFFSET :offset
        """
    )

    count_query = text(
        """
        SELECT COUNT(*)
        FROM ingestion_logs
        WHERE parent_log_id IS NULL
        """
    )

    with _get_engine().connect() as conn:
        try:
            rows = conn.execute(
                query,
                {"limit": page_size, "offset": offset},
            ).mappings().all()
            total_items = int(conn.execute(count_query).scalar_one())
        except (OperationalError, ProgrammingError):
            return [], 0

    return [dict(row) for row in rows], total_items


def fetch_child_ingestion_logs(parent_id: int, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    """Fetch paginated child logs linked to the given parent id."""
    offset = (page - 1) * page_size

    query = text(
        """
        SELECT
            id,
            parent_log_id,
            timestamp,
            source,
            COALESCE(details ->> 'database', 'postgres') AS database,
            event_type AS step,
            COALESCE(description, '') AS description
        FROM ingestion_logs
        WHERE parent_log_id = :parent_id
        ORDER BY timestamp DESC, id DESC
        LIMIT :limit OFFSET :offset
        """
    )

    count_query = text(
        """
        SELECT COUNT(*)
        FROM ingestion_logs
        WHERE parent_log_id = :parent_id
        """
    )

    with _get_engine().connect() as conn:
        try:
            rows = conn.execute(
                query,
                {"parent_id": parent_id, "limit": page_size, "offset": offset},
            ).mappings().all()
            total_items = int(
                conn.execute(count_query, {"parent_id": parent_id}).scalar_one()
            )
        except (OperationalError, ProgrammingError):
            return [], 0

    return [dict(row) for row in rows], total_items


def fetch_ingestion_log_by_id(log_id: int) -> dict[str, Any] | None:
    """Fetch one ingestion log by id."""
    query = text(
        """
        SELECT
            id,
            parent_log_id,
            timestamp,
            source,
            COALESCE(details ->> 'database', 'postgres') AS database,
            event_type,
            COALESCE(description, '') AS description,
            status
        FROM ingestion_logs
        WHERE id = :log_id
        LIMIT 1
        """
    )

    with _get_engine().connect() as conn:
        try:
            row = conn.execute(query, {"log_id": log_id}).mappings().first()
        except (OperationalError, ProgrammingError):
            return None

    if not row:
        return None

    return dict(row)
