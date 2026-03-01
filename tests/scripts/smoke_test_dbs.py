"""
Smoke test de integração.

Objetivo:
- Validar que o container da aplicação consegue ligar e executar operações mínimas
  nos 3 tipos de persistência do projeto:
  1) SQL: PostgreSQL
  2) NoSQL: MongoDB
  3) Vetorial: ChromaDB

Como executar (dentro do container da app):
    python tests/scripts/smoke_test_dbs.py

Este script faz operações reais (read/write/query) para garantir que os serviços
estão operacionais e que a comunicação entre containers está correta.
"""

import os
import time
from typing import Any

import chromadb
import psycopg
from pymongo import MongoClient


def env(name: str, default: str) -> str:
    """
    Lê uma variável de ambiente com fallback.

    Args:
        name: Nome da variável de ambiente.
        default: Valor por omissão caso a variável não exista.

    Returns:
        O valor da variável de ambiente se existir; caso contrário, `default`.
    """
    return os.getenv(name, default)


def test_postgres() -> None:
    """
    Testa conectividade e execução básica no PostgreSQL.

    Operações:
    - Conecta ao PostgreSQL usando parâmetros vindos do docker-compose (.env vars).
    - Executa `SELECT 1` para validar conexão e capacidade de correr queries.

    Raises:
        AssertionError: Se o resultado da query não for o esperado.
        psycopg.Error: Se houver erro de conexão/autenticação/rede.
    """
    host = env("POSTGRES_HOST", "ec-project-postgres")
    port = int(env("POSTGRES_PORT", "5432"))
    db = env("POSTGRES_DB", "ec_project")
    user = env("POSTGRES_USER", "ec_project")
    password = env("POSTGRES_PASSWORD", "ec_project_pass")

    conn_str = f"host={host} port={port} dbname={db} user={user} password={password}"

    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            val = cur.fetchone()
            assert val == (1,)
    print("Postgres OK (SELECT 1)")


def test_mongo() -> None:
    """
    Testa conectividade e read/write básico no MongoDB.

    Operações:
    - Cria cliente MongoDB e faz `ping` ao servidor.
    - Faz upsert de 1 documento na collection `smoke_test`.
    - Lê o documento e valida conteúdo.

    Raises:
        AssertionError: Se o documento não for lido ou tiver valores inesperados.
        pymongo.errors.PyMongoError: Se houver erro de conexão/rede/servidor.
    """
    host = env("MONGO_HOST", "ec-project-mongo")
    port = int(env("MONGO_PORT", "27017"))
    db_name = env("MONGO_DB", "ec_project")

    client = MongoClient(host=host, port=port, serverSelectionTimeoutMS=5000)
    # ping
    client.admin.command("ping")

    db = client[db_name]
    col = db["smoke_test"]

    # write + read
    doc: dict[str, Any] = {"_id": "hello", "msg": "world", "ts": time.time()}
    col.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    out = col.find_one({"_id": "hello"})
    assert out is not None and out.get("msg") == "world"
    print("Mongo OK (ping + insert + read)")


def test_chroma() -> None:
    """
    Testa conectividade e operação básica no Chroma (Vector DB) via HTTP.

    Operações:
    - Conecta ao servidor Chroma.
    - Cria/obtém a collection `smoke_test`.
    - Faz upsert de 1 documento com embedding "dummy".
    - Faz query com o mesmo embedding e valida que devolve o id esperado.

    Nota:
        O embedding usado é pequeno e artificial, só para validar o pipeline.

    Raises:
        AssertionError: Se o resultado da query não devolver o id esperado.
        Exception: Se houver erro de conexão ao servidor Chroma.
    """
    host = env("CHROMA_HOST", "ec-project-chroma")
    port = int(env("CHROMA_PORT", "8000"))

    # Chroma server client
    client = chromadb.HttpClient(host=host, port=port)

    # collection
    col = client.get_or_create_collection(name="smoke_test")

    # add 1 embedding "dummy"
    col.upsert(
        ids=["doc1"],
        documents=["hello world"],
        metadatas=[{"source": "smoke"}],
        embeddings=[[0.1, 0.2, 0.3, 0.4]],
    )

    # query
    res = col.query(
        query_embeddings=[[0.1, 0.2, 0.3, 0.4]],
        n_results=1,
    )
    assert res["ids"][0][0] == "doc1"
    print("Chroma OK (collection + upsert + query)")


def main() -> None:
    test_postgres()
    test_mongo()
    test_chroma()
    print("\nSmoke test OK: app liga a Postgres + Mongo + Chroma")


if __name__ == "__main__":
    main()
