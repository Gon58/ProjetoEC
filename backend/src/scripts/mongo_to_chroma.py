"""
Transferência de documentos do MongoDB para o ChromaDB com chunking e embeddings.

Este script segue a mesma estratégia do pipeline vetorial principal:
- extrai texto de cada documento
- divide o texto em chunks com overlap
- gera embeddings por chunk
- grava cada chunk no Chroma com metadados de origem

Usage (from repository root):
    python backend/src/scripts/mongo_to_chroma.py --collection steam_reviews --limit 300
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from pymongo import MongoClient

from src.db.vectorial import index_document

TEXT_CANDIDATE_FIELDS = ("review", "text", "content", "body", "description")
ID_CANDIDATE_FIELDS = ("recommendationid", "id", "_id")


def _resolve_doc_id(doc: dict[str, Any], collection_name: str) -> str:
    """Resolve um ID estável para o documento, priorizando campos semânticos."""
    for field in ID_CANDIDATE_FIELDS:
        if field in doc and doc[field] is not None:
            return f"{collection_name}:{str(doc[field])}"
    return f"{collection_name}:{str(doc.get('_id'))}"


def _resolve_text(doc: dict[str, Any], max_chars: int) -> str:
    """
    Extrai o texto mais relevante do documento para indexação.

    Prioriza campos textuais comuns (review/text/content/body/description).
    Caso nenhum exista, concatena todos os valores string do documento.
    """
    for field in TEXT_CANDIDATE_FIELDS:
        value = doc.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()[:max_chars]

    parts: list[str] = []
    for key, value in doc.items():
        if isinstance(value, str) and value.strip():
            parts.append(f"{key}: {value.strip()}")
    return "\n".join(parts)[:max_chars]


def _build_metadata(doc: dict[str, Any], collection_name: str) -> dict[str, Any]:
    """
    Constrói metadados serializáveis para o Chroma.

    Nota: Chroma suporta apenas tipos primitivos nos metadados.
    """
    metadata: dict[str, Any] = {
        "source_collection": collection_name,
        "source": str(doc.get("source", collection_name)),
    }

    for key in (
        "language",
        "is_market_related",
        "voted_up",
        "steam_purchase",
        "timestamp_created",
        "timestamp_updated",
    ):
        value = doc.get(key)
        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value

    return metadata


def transfer_mongo_to_chroma(
    mongo_host: str,
    mongo_port: int,
    mongo_db: str,
    mongo_collection: str,
    chroma_collection: str,
    limit: int | None,
    max_chars: int,
    chunk_size: int,
    overlap: int,
) -> dict[str, Any]:
    """
    Transfere dados de uma coleção Mongo para uma coleção Chroma.

    Esta função delega a indexação para src.db.vectorial.index_document,
    garantindo que o mesmo pipeline canónico (chunking + embeddings + gravação)
    é usado em toda a aplicação.

    Args:
        mongo_host: Host do MongoDB.
        mongo_port: Porta do MongoDB.
        mongo_db: Nome da base Mongo.
        mongo_collection: Coleção de origem no Mongo.
        chroma_collection: Coleção de destino no Chroma.
        limit: Limite opcional de documentos Mongo a processar.
        max_chars: Limite de caracteres por documento antes de chunking.
        chunk_size: Tamanho de cada chunk em caracteres.
        overlap: Sobreposição entre chunks consecutivos.

    Returns:
        Dicionário com métricas de processamento e indexação.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")

    if overlap < 0:
        raise ValueError("overlap must be >= 0")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    mongo_client = MongoClient(host=mongo_host, port=mongo_port, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command("ping")

    source_collection = mongo_client[mongo_db][mongo_collection]

    query: dict[str, Any] = {}
    cursor = source_collection.find(query)
    if limit:
        cursor = cursor.limit(limit)

    processed = 0
    skipped = 0
    indexed_chunks = 0

    for doc in cursor:
        processed += 1
        text = _resolve_text(doc, max_chars=max_chars)
        if not text:
            skipped += 1
            continue

        parent_doc_id = _resolve_doc_id(doc, mongo_collection)

        result = index_document(
            doc_id=parent_doc_id,
            text=text,
            collection_name=chroma_collection,
            metadata=_build_metadata(doc, mongo_collection),
            chunk_size=chunk_size,
            overlap=overlap,
        )

        if result.get("status") != "success":
            skipped += 1
            continue

        indexed_chunks += int(result.get("chunks_indexed", 0))

        if processed % 50 == 0:
            print(f"Processed {processed} documents | Indexed {indexed_chunks} chunks...")

    mongo_client.close()

    return {
        "status": "success",
        "processed_documents": processed,
        "indexed_chunks": indexed_chunks,
        "skipped": skipped,
        "mongo_collection": mongo_collection,
        "chroma_collection": chroma_collection,
        "chunk_size": chunk_size,
        "overlap": overlap,
    }


def parse_args() -> argparse.Namespace:
    """Define argumentos CLI para controlo de transferência e chunking."""
    parser = argparse.ArgumentParser(description="Transfer MongoDB docs to ChromaDB")
    parser.add_argument("--mongo-host", default=os.getenv("MONGO_HOST", "localhost"))
    parser.add_argument("--mongo-port", type=int, default=int(os.getenv("MONGO_PORT", "27017")))
    parser.add_argument("--mongo-db", default=os.getenv("MONGO_DB", "ec_project"))
    parser.add_argument("--collection", required=True, help="Mongo collection to read from")
    parser.add_argument("--chroma-collection", default="documents")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-chars", type=int, default=4000)
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--overlap", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    """Executa a transferência Mongo -> Chroma a partir dos argumentos CLI."""
    args = parse_args()

    result = transfer_mongo_to_chroma(
        mongo_host=args.mongo_host,
        mongo_port=args.mongo_port,
        mongo_db=args.mongo_db,
        mongo_collection=args.collection,
        chroma_collection=args.chroma_collection,
        limit=args.limit,
        max_chars=args.max_chars,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    print(result)


if __name__ == "__main__":
    main()
