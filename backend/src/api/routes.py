"""API routes for the backend."""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ..db.connections import check_chromadb, check_mongodb, check_postgres
from ..db.postgres import (
    fetch_best_selling_skinport_skins,
    fetch_history_skin_count,
    fetch_latest_data_timestamp,
    fetch_most_expensive_skinport_skins,
    fetch_price_history_for_top_skins,
    fetch_skin_price_history_by_id,
    fetch_skinport_skin_by_id,
    fetch_skinport_skins,
    fetch_steam_market_skins_for_browse,
    search_skins,
)
from ..db.vectorial import index_document, search_documents
from ..schemas.requests import ChatRequest, ChatResponse, DocumentIndexRequest, SearchRequest
from ..services.agent import chat_nesy_agent
from ..services.logs import fetch_logs

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
        collection_name=request.collection_name,
        n_results=request.n_results,
        distance_threshold=request.distance_threshold,
    )

    if result["status"] == "success":
        status_code = status.HTTP_200_OK
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    return JSONResponse(content=result, status_code=status_code)


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> JSONResponse:
    """Handles chat requests through the NeSy agent and returns safe API errors."""
    try:
        answer = chat_nesy_agent(request.message)
        payload = {
            "status": "success",
            "message": request.message,
            "answer": answer,
            "data_timestamp": fetch_latest_data_timestamp(),
        }
        return JSONResponse(content=payload, status_code=status.HTTP_200_OK)
    except Exception:
        payload = {
            "status": "error",
            "message": request.message,
            "answer": "Nao foi possível processar a mensagem neste momento.",
            "data_timestamp": None,
        }
        return JSONResponse(content=payload, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/skins")
def search_skins_endpoint(limit: int | None = None) -> JSONResponse:
    """
    Endpoint to get all skins for the web app.

    Fetches skins from the relational database and returns all results unless a limit is provided.

    Args:
        limit: Optional limit of results.
    Returns:
        JSON with query results.
    """
    try:
        result = fetch_skinport_skins(limit=limit)
        return JSONResponse(content=jsonable_encoder(result),
                             status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/skins/id/{skin_id}")
def get_skin_by_id(skin_id: int) -> JSONResponse:
    """
    Endpoint to get a specific skin by its ID.

    Args:
        skin_id: ID of the skin to retrieve.

    Returns:
        JSON with query results.
    """
    try:
        result = fetch_skinport_skin_by_id(skin_id=skin_id)
        if result:
            return JSONResponse(content=jsonable_encoder(result),
                                status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content={"error": "Skin not found"},
                    status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@router.get("/logs")
def get_logs_endpoint(
    parent_id: int | None = None,
    page: int = 1,
    page_size: int = 10,
) -> JSONResponse:
    """Return paginated logs for first level (parents) or second level (children)."""
    normalized_page = max(1, page)
    normalized_page_size = min(max(1, page_size), 100)

    result = fetch_logs(
        parent_id=parent_id,
        page=normalized_page,
        page_size=normalized_page_size,
    )
    return JSONResponse(content=jsonable_encoder(result), status_code=status.HTTP_200_OK)
    
@router.get("/skins/price-history")
def get_price_history(limit: int = 5, days: int = 30) -> JSONResponse:
    """
    Return price history for the top N most expensive skins over the last N days.

    Args:
        limit: Number of skins to include (default: 5).
        days: How many days of history to return (default: 30).
    """
    try:
        result = fetch_price_history_for_top_skins(limit=limit, days=days)
        return JSONResponse(content=jsonable_encoder(result), status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/skins/steam-market")
def get_steam_market_skins() -> JSONResponse:
    """Return all Steam Market skins with history (id, name, mean_price, quantity_sold)."""
    try:
        result = fetch_steam_market_skins_for_browse()
        return JSONResponse(content=jsonable_encoder(result), status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/skins/history-count")
def get_history_skin_count() -> JSONResponse:
    """Return the number of skins that have price history."""
    try:
        count = fetch_history_skin_count()
        return JSONResponse(content={"count": count}, status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/skins/search")
def search_skins_endpoint(q: str = "", limit: int = 10) -> JSONResponse:
    """Search skins by name across all sources."""
    if not q or len(q.strip()) < 2:
        return JSONResponse(content=[], status_code=status.HTTP_200_OK)
    try:
        result = search_skins(q=q.strip(), limit=limit)
        return JSONResponse(content=jsonable_encoder(result), status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/skins/{skin_id}/history")
def get_skin_history(skin_id: int, days: int = 30) -> JSONResponse:
    """
    Return the price history for a single skin.

    Args:
        skin_id: ID of the skin.
        days: How many days of history to return (default: 30).
    """
    try:
        result = fetch_skin_price_history_by_id(skin_id=skin_id, days=days)
        if not result:
            return JSONResponse(content={"error": "No history found for this skin"},
                                status_code=status.HTTP_404_NOT_FOUND)
        return JSONResponse(content=jsonable_encoder(result), status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/skins/most-expensive")
def get_most_expensive_skins(limit: int = 10) -> JSONResponse:
    """
    Endpoint to get the most expensive skins.

    Args:
        limit: Number of top expensive skins to retrieve (default: 10).

    Returns:
        JSON with query results.
    """
    try:
        result = fetch_most_expensive_skinport_skins(limit=limit)
        return JSONResponse(content=jsonable_encoder(result),
                            status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/skins/best-selling")
def get_best_selling_skins(limit: int = 10) -> JSONResponse:
    """
    Endpoint to get the best selling skins.

    Args:
        limit: Number of best selling skins to retrieve (default: 10).

    Returns:
        JSON with query results.
    """
    try:
        result = fetch_best_selling_skinport_skins(limit=limit)
        return JSONResponse(content=jsonable_encoder(result),
                            status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
