from typing import Any, Dict

import chromadb
import psycopg
from pymongo import MongoClient

from ..core.config import CHROMA_HOST, CHROMA_PORT, MONGO_HOST, MONGO_PORT, POSTGRES_URL


def check_postgres() -> Dict[str, Any]:
    """Checks connection to PostgreSQL."""
    try:
        postgres_url_limpo = (POSTGRES_URL or "").replace(
            "postgresql+psycopg://",
            "postgresql://",
        )
        with psycopg.connect(postgres_url_limpo, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"status": "up", "message": "Connected"}
    except Exception as e:
        return {"status": "down", "message": str(e)}


def check_mongodb() -> Dict[str, Any]:
    """Checks connection to MongoDB."""
    try:
        client = MongoClient(
            host=MONGO_HOST,
            port=MONGO_PORT,
            serverSelectionTimeoutMS=3000
        )
        client.admin.command("ping")
        client.close()
        return {"status": "up", "message": "Connected"}
    except Exception as e:
        return {"status": "down", "message": str(e)}


def check_chromadb() -> Dict[str, Any]:
    """Checks connection to ChromaDB."""
    try:
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT
        )
        client.heartbeat()
        return {"status": "up", "message": "Connected"}
    except Exception as e:
        return {"status": "down", "message": str(e)}


def get_chroma_client() -> chromadb.HttpClient:
    """Gets a ChromaDB client configured with host and port from the environment."""
    return chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
