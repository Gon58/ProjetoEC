"""
Vector search operations using ChromaDB and Ollama embeddings.

Provides functions to index documents and perform semantic searches
using embeddings generated via Ollama (embeddinggemma).
"""

from typing import Any, Dict

from ..core.config import MIN_CHUNK_LENGTH, SEARCH_DISTANCE_THRESHOLD
from ..services.embeddings import EmbeddingError, embed_text, embed_texts
from .connections import get_chroma_client


def index_document(
    doc_id: str,
    text: str,
    collection_name: str = "documents",
    metadata: Dict[str, Any] | None = None,
    chunk_size: int = 512,
    overlap: int = 100,
) -> Dict[str, Any]:
    """
    Indexes a document in ChromaDB with embeddings generated via Ollama (embeddinggemma).

    Splits the document into overlapping chunks, generates embeddings for each chunk,
    and stores them in ChromaDB.

    Args:
        doc_id: Unique identifier for the document.
        text: Content of the document to index.
        collection_name: Name of the collection in ChromaDB.
        metadata: Additional metadata about the document.
        chunk_size: Size of each chunk in characters.
        overlap: Overlap between chunks to maintain context.

    Returns:
        Dictionary with indexing result: doc_id, chunks_indexed, status.

    Raises:
        Exception: If indexing fails.
    """
    try:
        if chunk_size <= 0:
            return {"status": "error", "message": "chunk_size must be greater than zero"}

        if overlap < 0 or overlap >= chunk_size:
            return {"status": "error", "message": "overlap must be >= 0 and < chunk_size"}

        if metadata is None:
            metadata = {}

        normalized_text = " ".join(text.split())
        if not normalized_text:
            return {"status": "error", "message": "Document text is empty after normalization"}

        # Split the document into chunks
        chunks = []
        for i in range(0, len(normalized_text), chunk_size - overlap):
            chunk = normalized_text[i : i + chunk_size]
            if len(chunk) >= MIN_CHUNK_LENGTH:
                chunks.append(chunk)

        if not chunks:
            return {
                "status": "error",
                "message": "No chunks created after min_chunk_length filtering",
            }

        # Generate embeddings for the chunks
        embeddings = embed_texts(chunks)

        # Prepare IDs and metadata for chunks
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        chunk_metadatas = [
            {**metadata, "doc_id": doc_id, "chunk_index": i}
            for i in range(len(chunks))
        ]

        # Store in ChromaDB
        client = get_chroma_client()
        collection = client.get_or_create_collection(name=collection_name)
        collection.add(
            ids=chunk_ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=chunk_metadatas,
        )

        return {
            "status": "success",
            "doc_id": doc_id,
            "chunks_indexed": len(chunks),
        }
    except EmbeddingError as exc:
        return {
            "status": "error",
            "error_code": "embedding_failure",
            "message": str(exc),
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def search_documents(
    query: str,
    collection_name: str = "documents",
    n_results: int = 5,
    distance_threshold: float | None = SEARCH_DISTANCE_THRESHOLD,
) -> Dict[str, Any]:
    """
    Searches documents in ChromaDB using semantic vector search.

    Generates embedding for the query using Ollama (embeddinggemma) and finds
    the most similar documents in ChromaDB.

    Args:
        query: Text of the query for semantic search.
        collection_name: Name of the collection in ChromaDB.
        n_results: Number of results to return.
        distance_threshold: Maximum accepted distance for returned chunks.

    Returns:
        Dictionary with search results: query, results, total_results.

    Raises:
        Exception: If search fails.
    """
    try:
        # Generate embedding for the query
        query_embedding = embed_text(query)

        # Search in ChromaDB
        client = get_chroma_client()
        collection = client.get_or_create_collection(name=collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        # Format results
        formatted_results = []
        if results["ids"] and len(results["ids"]) > 0:
            for idx, (chunk_id, distance) in enumerate(
                zip(results["ids"][0], results["distances"][0])
            ):
                numeric_distance = float(distance)
                if distance_threshold is not None and numeric_distance > distance_threshold:
                    continue

                formatted_results.append({
                    "chunk_id": chunk_id,
                    "text": results["documents"][0][idx],
                    "distance": numeric_distance,
                    "metadata": results["metadatas"][0][idx],
                })

        return {
            "status": "success",
            "query": query,
            "collection_name": collection_name,
            "total_results": len(formatted_results),
            "results": formatted_results,
            "distance_threshold": distance_threshold,
        }
    except EmbeddingError as exc:
        # Stable fallback for API/tool callers when embeddings are unavailable.
        return {
            "status": "success",
            "query": query,
            "collection_name": collection_name,
            "total_results": 0,
            "results": [],
            "distance_threshold": distance_threshold,
            "fallback": {
                "active": True,
                "reason_code": "embedding_failure",
                "message": str(exc),
            },
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
