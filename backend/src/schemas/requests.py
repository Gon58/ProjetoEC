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


class ChatRequest(BaseModel):
    """Modelo para pedido de chat do frontend para o agente NeSy."""
    message: str


class ChatResponse(BaseModel):
    """Modelo de resposta do endpoint de chat do agente."""
    status: str
    message: str
    answer: str