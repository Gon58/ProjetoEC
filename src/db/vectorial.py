"""
Operações de busca vetorial usando ChromaDB e Ollama embeddings.

Fornece funções para indexar documentos e realizar buscas semânticas
utilizando embeddings gerados via Ollama (embeddinggemma).
"""

from typing import Any, Dict

from src.db.connections import get_chroma_client
from src.services.embeddings import embed_text, embed_texts


def index_document(
    doc_id: str,
    text: str,
    collection_name: str = "documents",
    metadata: Dict[str, Any] | None = None,
    chunk_size: int = 512,
    overlap: int = 100,
) -> Dict[str, Any]:
    """
    Indexa um documento no ChromaDB com embeddings gerados via Ollama (embeddinggemma).

    Divide o documento em chunks sobrepostos, gera embeddings para cada chunk,
    e armazena no ChromaDB.

    Args:
        doc_id: Identificador único do documento.
        text: Conteúdo do documento a indexar.
        collection_name: Nome da coleção no ChromaDB.
        metadata: Metadados adicionais sobre o documento.
        chunk_size: Tamanho de cada chunk em caracteres.
        overlap: Sobreposição entre chunks para manter contexto.

    Returns:
        Dicionário com resultado da indexação: doc_id, chunks_indexed, status.

    Raises:
        Exception: Se a indexação falhar.
    """
    try:
        if metadata is None:
            metadata = {}

        # Divide o documento em chunks
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i : i + chunk_size])

        if not chunks:
            return {"status": "error", "message": "No chunks created"}

        # Gera embeddings para os chunks
        embeddings = embed_texts(chunks)

        # Prepara IDs e metadados dos chunks
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        chunk_metadatas = [
            {**metadata, "doc_id": doc_id, "chunk_index": i}
            for i in range(len(chunks))
        ]

        # Armazena no ChromaDB
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
    Pesquisa documentos no ChromaDB usando búsca vetorial semântica.

    Gera embedding para a query usando Ollama (embeddinggemma) e procura
    os documentos mais similares no ChromaDB.

    Args:
        query: Texto da query para pesquisa semântica.
        collection_name: Nome da coleção no ChromaDB.
        n_results: Número de resultados a retornar.

    Returns:
        Dicionário com resultados da pesquisa: query, results, total_results.

    Raises:
        Exception: Se a pesquisa falhar.
    """
    try:
        # Gera embedding para a query
        query_embedding = embed_text(query)

        # Pesquisa no ChromaDB
        client = get_chroma_client()
        collection = client.get_or_create_collection(name=collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        # Formata resultados
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
