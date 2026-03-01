import os
from datetime import datetime, timezone
from typing import Any, Dict

import chromadb
import psycopg
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pymongo import MongoClient

from src.db.connections import check_postgres, check_mongodb, check_chromadb

app = FastAPI(title="API Backend")

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
