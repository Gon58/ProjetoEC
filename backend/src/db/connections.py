import os
from typing import Any, Dict

import chromadb
import psycopg
from pymongo import MongoClient


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
        client.heartbeat()
        return {"status": "up", "message": "Connected"}
    except Exception as e:
        return {"status": "down", "message": str(e)}


def get_chroma_client() -> chromadb.HttpClient:
    """Obtém um cliente ChromaDB configurado com host e porta do ambiente."""
    chroma_host = os.getenv("CHROMA_HOST", "localhost")
    chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
    return chromadb.HttpClient(host=chroma_host, port=chroma_port)
