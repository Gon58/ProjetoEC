from typing import Any

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

from ..core.config import POSTGRES_URL


def _get_engine():
    """Creates engine from POSTGRES_URL."""
    if not POSTGRES_URL:
        raise ValueError("POSTGRES_URL is not configured")
    return create_engine(POSTGRES_URL, echo=False)


def fetch_skinport_skins(limit: int | None = None) -> list[dict[str, Any]]:
    """Fetch all skin rows from PostgreSQL (all sources)."""
    query = """
        SELECT id, name, currency, min_price, max_price, mean_price,
               median_price, quantity_sold, source
        FROM skin
        ORDER BY mean_price DESC
    """
    params: dict[str, Any] = {}
    if limit is not None:
        query += "\n        LIMIT :limit"
        params["limit"] = limit

    with _get_engine().connect() as conn:
        rows = conn.execute(text(query), params).mappings().all()
    return [dict(row) for row in rows]


def fetch_steam_market_skins_for_browse() -> list[dict[str, Any]]:
    """Return all Steam Market skins that have price history (minimal fields for browse panel)."""
    query = text("""
        SELECT DISTINCT ON (s.id) s.id, s.name, s.mean_price, s.quantity_sold
        FROM skin s
        INNER JOIN skin_price_history sph ON sph.skin_id = s.id
        ORDER BY s.id, s.mean_price DESC
    """)
    with _get_engine().connect() as conn:
        try:
            rows = conn.execute(query).mappings().all()
        except Exception:
            return []
    return [dict(row) for row in rows]


def search_skins(q: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search skins by name — only returns skins that have price history."""
    query = text("""
        SELECT DISTINCT ON (s.id)
               s.id, s.name, s.currency, s.min_price, s.max_price, s.mean_price,
               s.median_price, s.quantity_sold, s.source
        FROM skin s
        INNER JOIN skin_price_history sph ON sph.skin_id = s.id
        WHERE LOWER(s.name) LIKE LOWER(:pattern)
        ORDER BY s.id, s.mean_price DESC
        LIMIT :limit
    """)
    with _get_engine().connect() as conn:
        rows = conn.execute(query, {"pattern": f"%{q}%", "limit": limit}).mappings().all()
    return [dict(row) for row in rows]


def fetch_history_skin_count() -> int:
    """Return the number of distinct skins that have price history."""
    query = text("SELECT COUNT(DISTINCT skin_id) FROM skin_price_history")
    with _get_engine().connect() as conn:
        try:
            return int(conn.execute(query).scalar_one())
        except Exception:
            return 0


def fetch_skinport_skin_by_name(name: str) -> dict[str, Any] | None:
    """Fetch one Skinport skin by exact name from PostgreSQL."""
    query = text("""
        SELECT id, name, currency, min_price, max_price, mean_price,
               median_price, quantity_sold, source
        FROM skin
        WHERE source = :source AND name = :name
        LIMIT 1
    """)

    with _get_engine().connect() as conn:
        row = (
            conn.execute(query, {"source": "skinport", "name": name})
            .mappings()
            .first()
        )

    if not row:
        return None

    return dict(row)

def fetch_skinport_skin_by_id(skin_id: int) -> dict[str, Any] | None:
    """Fetch one Skinport skin by its id from PostgreSQL."""
    query = text("""
        SELECT id, name, currency, min_price, max_price, mean_price,
               median_price, quantity_sold, source
        FROM skin
        WHERE source = :source AND id = :skin_id
        LIMIT 1
    """)

    with _get_engine().connect() as conn:
        row = (
            conn.execute(query, {"source": "skinport", "skin_id": skin_id})
            .mappings()
            .first()
        )

    if not row:
        return None

    return dict(row)

def fetch_most_expensive_skinport_skins(
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Fetch the most expensive Skinport skins."""
    query = text("""
        SELECT id, name, currency, min_price, max_price, mean_price,
               median_price, quantity_sold, source
        FROM skin
        WHERE source = :source
        ORDER BY mean_price DESC
        LIMIT :limit
    """)

    with _get_engine().connect() as conn:
        rows = conn.execute(
            query, {"source": "skinport", "limit": limit}
        ).mappings().all()
    return [dict(row) for row in rows]

def fetch_best_selling_skinport_skins(
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Fetch the best selling Skinport skins."""
    query = text("""
        SELECT id, name, currency, min_price, max_price, mean_price,
               median_price, quantity_sold, source
        FROM skin
        WHERE source = :source
        ORDER BY quantity_sold DESC
        LIMIT :limit
    """)

    with _get_engine().connect() as conn:
        rows = conn.execute(
            query, {"source": "skinport", "limit": limit}
        ).mappings().all()
    return [dict(row) for row in rows]

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


def fetch_child_ingestion_logs(
    parent_id: int,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
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


def fetch_latest_data_timestamp() -> str | None:
    """Return the most recent recorded_at from skin_price_history, or last_updated from skin."""
    query = text("""
        SELECT COALESCE(
            (SELECT MAX(recorded_at) FROM skin_price_history),
            (SELECT MAX(last_updated) FROM skin WHERE source = 'skinport')
        ) AS ts
    """)
    with _get_engine().connect() as conn:
        try:
            row = conn.execute(query).one_or_none()
        except Exception:
            return None
    if row is None or row.ts is None:
        return None
    dt = row.ts
    months = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    ]
    return f"{dt.day} de {months[dt.month - 1]} de {dt.year}, às {dt.strftime('%H:%M')}"


def fetch_price_history_for_top_skins(limit: int = 5, days: int = 30) -> list[dict[str, Any]]:
    """Return the price history of the top N most expensive skins that have history."""
    query = text("""
        WITH skins_with_history AS (
            SELECT DISTINCT sph.skin_id, s.mean_price
            FROM skin_price_history sph
            JOIN skin s ON s.id = sph.skin_id
            WHERE s.mean_price > 0
        ),
        top_skins AS (
            SELECT skin_id AS id
            FROM skins_with_history
            ORDER BY mean_price DESC
            LIMIT :limit
        )
        SELECT
            ts.id AS skin_id,
            sph.skin_name,
            to_char(sph.recorded_at, 'YYYY-MM-DD') AS date,
            sph.mean_price
        FROM top_skins ts
        JOIN skin_price_history sph ON sph.skin_id = ts.id
        WHERE sph.recorded_at >= NOW() - (:days || ' days')::INTERVAL
        ORDER BY ts.id, sph.recorded_at
    """)
    with _get_engine().connect() as conn:
        try:
            rows = conn.execute(query, {"limit": limit, "days": days}).mappings().all()
        except Exception:
            return []

    grouped: dict[int, dict[str, Any]] = {}
    for row in rows:
        sid = row["skin_id"]
        if sid not in grouped:
            grouped[sid] = {"skin_id": sid, "skin_name": row["skin_name"], "history": []}
        grouped[sid]["history"].append(
            {"date": row["date"], "mean_price": float(row["mean_price"] or 0)}
        )
    return list(grouped.values())


def fetch_skin_price_history_by_id(skin_id: int, days: int = 30) -> list[dict[str, Any]]:
    """Return daily price history for a single skin."""
    query = text("""
        SELECT
            to_char(recorded_at, 'YYYY-MM-DD') AS date,
            mean_price,
            min_price,
            max_price
        FROM skin_price_history
        WHERE skin_id = :skin_id
          AND recorded_at >= NOW() - (:days || ' days')::INTERVAL
        ORDER BY recorded_at
    """)
    with _get_engine().connect() as conn:
        try:
            rows = conn.execute(query, {"skin_id": skin_id, "days": days}).mappings().all()
        except Exception:
            return []
    return [
        {
            "date": r["date"],
            "mean_price": float(r["mean_price"] or 0),
            "min_price": float(r["min_price"] or 0),
            "max_price": float(r["max_price"] or 0),
        }
        for r in rows
    ]


def fetch_price_changes_for_names(names: list[str], days: int = 14) -> dict[str, dict[str, Any]]:
    """For each skin name, return its latest price and the % change over the last N days.

    Matches inventory item names against `skin_price_history.skin_name`. The window is
    anchored to the most recent record in the table (not NOW()), so it stays correct
    even when the data is older than `days`. Names with no history are simply omitted.

    Returns a dict keyed by skin_name: {"current_price", "start_price", "change_pct", "recorded_at"}.
    """
    if not names:
        return {}

    query = text("""
        WITH filtered AS (
            SELECT sph.skin_name, sph.recorded_at, sph.mean_price
            FROM skin_price_history sph
            WHERE sph.skin_name IN :names
              AND sph.recorded_at >= NOW() - (:days || ' days')::INTERVAL
        ),
        ranked AS (
            SELECT
                skin_name,
                FIRST_VALUE(mean_price) OVER w_desc AS current_price,
                FIRST_VALUE(mean_price) OVER w_asc  AS start_price,
                FIRST_VALUE(recorded_at) OVER w_desc AS recorded_at
            FROM filtered
            WINDOW
                w_desc AS (PARTITION BY skin_name ORDER BY recorded_at DESC),
                w_asc  AS (PARTITION BY skin_name ORDER BY recorded_at ASC)
        )
        SELECT DISTINCT skin_name, current_price, start_price, recorded_at
        FROM ranked
    """).bindparams(bindparam("names", expanding=True))

    with _get_engine().connect() as conn:
        try:
            rows = conn.execute(query, {"names": names, "days": days}).mappings().all()
        except Exception:
            return {}

    result: dict[str, dict[str, Any]] = {}
    for r in rows:
        current = float(r["current_price"] or 0)
        start = float(r["start_price"] or 0)
        change_pct = ((current - start) / start * 100) if start > 0 else 0.0
        result[r["skin_name"]] = {
            "current_price": current,
            "start_price": start,
            "change_pct": round(change_pct, 2),
            "recorded_at": r["recorded_at"].isoformat() if r["recorded_at"] else None,
        }
    return result


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
