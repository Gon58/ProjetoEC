"""Pydantic models for API requests."""

from typing import Any

from pydantic import BaseModel, Field

from ..core.config import RAG_COLLECTION_NAME


class DocumentIndexRequest(BaseModel):
    """Modelo para requisição de indexação de documento."""
    doc_id: str
    text: str
    metadata: dict[str, Any] | None = None


class SearchRequest(BaseModel):
    """Modelo para requisição de busca vetorial."""
    query: str
    n_results: int = Field(default=5, ge=1, le=20)
    collection_name: str = RAG_COLLECTION_NAME
    distance_threshold: float | None = Field(default=None, ge=0.0)


class ChatRequest(BaseModel):
    """Modelo para pedido de chat do frontend para o agente NeSy."""
    message: str


class ChatResponse(BaseModel):
    """Modelo de resposta do endpoint de chat do agente."""
    status: str
    message: str
    answer: str
    data_timestamp: str | None = None