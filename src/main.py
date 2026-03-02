from datetime import datetime, timezone

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.db.connections import check_chromadb, check_mongodb, check_postgres
from src.db.vectorial import index_document, search_documents

app = FastAPI(title="API Backend")


# Modelos Pydantic para requisições de busca vetorial
class DocumentIndexRequest(BaseModel):
    """Modelo para requisição de indexação de documento."""
    doc_id: str
    text: str
    metadata: dict | None = None


class SearchRequest(BaseModel):
    """Modelo para requisição de busca vetorial."""
    query: str
    n_results: int = 5


@app.get("/health")
def health_check():
    """
    Health check endpoint que verifica:
    - Status da API
    - Conexão com PostgreSQL
    - Conexão com MongoDB
    - Conexão com ChromaDB
    """
    checks = {
        "postgres": check_postgres(),
        "mongodb": check_mongodb(),
        "chromadb": check_chromadb(),
    }

    # Determina se todos os serviços estão UP
    all_healthy = all(check["status"] == "up" for check in checks.values())

    response_data = {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "checks": checks,
    }

    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=response_data, status_code=status_code)


@app.post("/index")
def index_document_endpoint(request: DocumentIndexRequest):
    """
    Endpoint para indexar um documento no ChromaDB.

    Divide o documento em chunks, gera embeddings via Ollama,
    e armazena no ChromaDB para busca vetorial posterior.

    Args:
        request: Objeto com doc_id, text, e metadados opcionais.

    Returns:
        JSON com status, doc_id, e número de chunks indexados.
    """
    result = index_document(
        doc_id=request.doc_id,
        text=request.text,
        metadata=request.metadata,
    )
    
    status_code = status.HTTP_200_OK if result["status"] == "success" else status.HTTP_400_BAD_REQUEST
    return JSONResponse(content=result, status_code=status_code)


@app.post("/search")
def search_documents_endpoint(request: SearchRequest):
    """
    Endpoint para pesquisa vetorial semântica no ChromaDB.

    Gera embedding para a query e retorna documentos similares
    ordenados por relevância (distância).

    Args:
        request: Objeto com query e n_results (padrão: 5).

    Returns:
        JSON com query, resultados e número total de matches.
    """
    result = search_documents(
        query=request.query,
        n_results=request.n_results,
    )
    
    status_code = status.HTTP_200_OK if result["status"] == "success" else status.HTTP_400_BAD_REQUEST
    return JSONResponse(content=result, status_code=status_code)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
