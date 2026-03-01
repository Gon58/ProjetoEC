import os
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import psycopg
from pymongo import MongoClient
import chromadb

app = FastAPI(title="API Backend")


def check_postgres() -> Dict[str, Any]:
    """Verifica conexão com PostgreSQL."""
    try:
        conn_string = (
            f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
            f"port={os.getenv('POSTGRES_PORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB', 'ec_project')} "
            f"user={os.getenv('POSTGRES_USER', 'ec_project')} "
            f"password={os.getenv('POSTGRES_PASSWORD', '')} "
            f"connect_timeout=3"
        )
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"status": "up", "message": "Connected"}
    except Exception as e:
        return {"status": "down", "message": str(e)}


def check_mongodb() -> Dict[str, Any]:
    """Verifica conexão com MongoDB."""
    try:
        mongo_host = os.getenv("MONGO_HOST", "localhost")
        mongo_port = int(os.getenv("MONGO_PORT", "27017"))
        client = MongoClient(
            host=mongo_host,
            port=mongo_port,
            serverSelectionTimeoutMS=3000
        )
        # Ping para verificar conexão
        client.admin.command("ping")
        client.close()
        return {"status": "up", "message": "Connected"}
    except Exception as e:
        return {"status": "down", "message": str(e)}


def check_chromadb() -> Dict[str, Any]:
    """Verifica conexão com ChromaDB."""
    try:
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port
        )
        # Heartbeat para verificar se está respondendo
        client.heartbeat()
        return {"status": "up", "message": "Connected"}
    except Exception as e:
        return {"status": "down", "message": str(e)}


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
        "checks": checks
    }
    
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(content=response_data, status_code=status_code)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
