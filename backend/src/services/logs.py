"""Logs service backed by PostgreSQL ingestion_logs table."""

from __future__ import annotations

from typing import Any

from ..db.postgres import (
    fetch_child_ingestion_logs,
    fetch_ingestion_log_by_id,
    fetch_parent_ingestion_logs,
)


def _build_pagination(page: int, page_size: int, total_items: int) -> dict[str, Any]:
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    bounded_page = min(max(1, page), total_pages)
    return {
        "page": bounded_page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_prev": bounded_page > 1,
        "has_next": bounded_page < total_pages,
    }


def fetch_logs(parent_id: int | None, page: int, page_size: int) -> dict[str, Any]:
    """Fetch logs for level 1 (parents) or level 2 (children) with pagination."""
    if parent_id is None:
        parent_rows, total_items = fetch_parent_ingestion_logs(page=page, page_size=page_size)
        items = [
            {
                **row,
                "has_children": int(row.get("children_count", 0)) > 0,
            }
            for row in parent_rows
        ]
        return {
            "level": "parent",
            "parent_id": None,
            "items": items,
            "pagination": _build_pagination(
                page=page,
                page_size=page_size,
                total_items=total_items,
            ),
        }

    child_rows, total_items = fetch_child_ingestion_logs(
        parent_id=parent_id,
        page=page,
        page_size=page_size,
    )
    parent = fetch_ingestion_log_by_id(parent_id)

    return {
        "level": "child",
        "parent_id": parent_id,
        "parent": parent,
        "items": child_rows,
        "pagination": _build_pagination(
            page=page,
            page_size=page_size,
            total_items=total_items,
        ),
    }
