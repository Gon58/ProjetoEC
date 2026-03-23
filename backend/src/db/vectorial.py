"""
Vector search operations using ChromaDB and Ollama embeddings.

Provides functions to index documents and perform semantic searches
using embeddings generated via Ollama (embeddinggemma).
"""

from typing import Any, Dict

from ..services.embeddings import embed_text, embed_texts
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
        if metadata is None:
            metadata = {}

        # Split the document into chunks
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i : i + chunk_size])

        if not chunks:
            return {"status": "error", "message": "No chunks created"}

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
    except Exception as e:
        return {"status": "error", "message": str(e)}


def search_documents(
    query: str,
    collection_name: str = "documents",
    n_results: int = 5,
) -> Dict[str, Any]:
    """
    Searches documents in ChromaDB using semantic vector search.

    Generates embedding for the query using Ollama (embeddinggemma) and finds
    the most similar documents in ChromaDB.

    Args:
        query: Text of the query for semantic search.
        collection_name: Name of the collection in ChromaDB.
        n_results: Number of results to return.

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
                formatted_results.append({
                    "chunk_id": chunk_id,
                    "text": results["documents"][0][idx],
                    "distance": float(distance),
                    "metadata": results["metadatas"][0][idx],
                })

        return {
            "status": "success",
            "query": query,
            "total_results": len(formatted_results),
            "results": formatted_results,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
