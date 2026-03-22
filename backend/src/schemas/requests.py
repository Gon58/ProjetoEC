"""Pydantic models for API requests."""

from typing import Dict, Optional

from pydantic import BaseModel


class DocumentIndexRequest(BaseModel):
    """Modelo para requisição de indexação de documento."""
    doc_id: str
    text: str
    metadata: Optional[Dict] = None


class SearchRequest(BaseModel):
    """Modelo para requisição de busca vetorial."""
    query: str
    n_results: int = 5