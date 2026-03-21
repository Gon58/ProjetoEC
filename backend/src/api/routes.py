"""API routes for the backend."""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from ..db.connections import check_chromadb, check_mongodb, check_postgres
from ..db.vectorial import index_document, search_documents
from ..schemas.requests import DocumentIndexRequest, SearchRequest

router = APIRouter()


@router.get("/health")
def health_check() -> JSONResponse:
    """
    Health check endpoint that verifies:
    - API status
    - Connection to PostgreSQL
    - Connection to MongoDB
    - Connection to ChromaDB
    """
    checks: Dict[str, Dict[str, Any]] = {
        "postgres": check_postgres(),
        "mongodb": check_mongodb(),
        "chromadb": check_chromadb(),
    }

    # Determine if all services are UP
    all_healthy = all(check["status"] == "up" for check in checks.values())

    response_data = {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "checks": checks,
    }

    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=response_data, status_code=status_code)


@router.post("/index")
def index_document_endpoint(request: DocumentIndexRequest) -> JSONResponse:
    """
    Endpoint to index a document in ChromaDB.

    Splits the document into chunks, generates embeddings via Ollama,
    and stores in ChromaDB for later vector search.

    Args:
        request: Object with doc_id, text, and optional metadata.

    Returns:
        JSON with status, doc_id, and number of indexed chunks.
    """
    result = index_document(
        doc_id=request.doc_id,
        text=request.text,
        metadata=request.metadata,
    )

    if result["status"] == "success":
        status_code = status.HTTP_200_OK
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return JSONResponse(content=result, status_code=status_code)


@router.post("/search")
def search_documents_endpoint(request: SearchRequest) -> JSONResponse:
    """
    Endpoint for semantic vector search in ChromaDB.

    Generates embedding for the query and returns similar documents
    ordered by relevance (distance).

    Args:
        request: Object with query and n_results (default: 5).

    Returns:
        JSON with query, results, and total number of matches.
    """
    result = search_documents(
        query=request.query,
        n_results=request.n_results,
    )

    if result["status"] == "success":
        status_code = status.HTTP_200_OK
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    return JSONResponse(content=result, status_code=status_code)


@router.get("/skins")
def search_skins_endpoint(limit: int = 100) -> JSONResponse:
    """
    Endpoint para ir buscar as skins para a web App.

    Vai buscar as skins à base de dados relacional e retorna 100 resultados

    Args:
        limit: Limite de resultados (padrão: 100).

    Returns:
        JSON resultados.
    """
    result = fetch_skinport_skins(limit=limit)
    return JSONResponse(content=jsonable_encoder(result), status_code=status.HTTP_200_OK)