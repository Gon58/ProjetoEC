"""
Script de teste para validar o modelo de embedding (embeddinggemma).

Testa o pipeline completo de:
1. Download automático do modelo
2. Geração de embeddings
3. Indexação no ChromaDB
4. Busca vetorial semântica
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.connections import get_chroma_client  # noqa: E402
from src.db.vectorial import index_document, search_documents  # noqa: E402
from src.services.embeddings import embed_text, embed_texts, ensure_model  # noqa: E402


def test_embedding_pipeline() -> bool:
    """
    Testa o pipeline completo com embeddinggemma.

    Returns:
        True se todos os testes passaram, False caso contrário.
    """
    print(f"\n{'='*60}")
    print("Testando pipeline de embedding (embeddinggemma)")
    print(f"{'='*60}")

    try:
        # 1. Teste: Garantir que modelo está disponível
        print("\n[1/5] Verificando/baixando modelo 'embeddinggemma'...")
        ensure_model("embeddinggemma")
        print("✓ Modelo 'embeddinggemma' disponível")

        # 2. Teste: Embedding de texto único
        print("\n[2/5] Gerando embedding para texto único...")
        text_single = "Machine learning is transforming technology"
        embedding_single = embed_text(text_single)
        print(f"✓ Embedding gerado: {len(embedding_single)} dimensões")
        
        if len(embedding_single) == 0:
            print("✗ ERRO: Embedding vazio")
            return False

        # 3. Teste: Embeddings de múltiplos textos
        print("\n[3/5] Gerando embeddings para múltiplos textos...")
        texts_batch = [
            "Artificial intelligence in healthcare",
            "Deep learning for computer vision",
            "Natural language processing applications",
        ]
        embeddings_batch = embed_texts(texts_batch)
        print(f"✓ {len(embeddings_batch)} embeddings gerados")
        
        if len(embeddings_batch) != len(texts_batch):
            print("✗ ERRO: Número de embeddings não corresponde aos textos")
            return False

        # 4. Teste: Indexação no ChromaDB
        print("\n[4/5] Indexando documentos no ChromaDB...")
        collection_name = "test_embeddings"
        
        # Limpa coleção anterior se existir
        try:
            client = get_chroma_client()
            client.delete_collection(collection_name)
        except Exception:
            pass  # Coleção não existe, tudo bem
        
        doc_text = """
        Machine learning is a subset of artificial intelligence that focuses on 
        developing systems that can learn from and make decisions based on data. 
        Deep learning, a subfield of machine learning, uses neural networks with 
        multiple layers to process complex patterns in large amounts of data.
        """ * 3  # Texto maior para gerar múltiplos chunks
        
        result = index_document(
            doc_id="test_doc",
            text=doc_text,
            collection_name=collection_name,
            metadata={"test": True},
        )
        
        if result["status"] != "success":
            print(f"✗ ERRO na indexação: {result.get('message', 'Unknown error')}")
            return False
        
        print(f"✓ Documento indexado: {result['chunks_indexed']} chunks")

        # 5. Teste: Busca vetorial
        print("\n[5/5] Executando busca vetorial...")
        search_result = search_documents(
            query="What is deep learning?",
            collection_name=collection_name,
            n_results=3,
        )
        
        if search_result["status"] != "success":
            print(f"✗ ERRO na busca: {search_result.get('message', 'Unknown error')}")
            return False
        
        print(f"✓ Busca retornou {search_result['total_results']} resultados")
        
        # Mostra resultados
        if search_result['total_results'] > 0:
            print(f"\nMelhor match (distância: {search_result['results'][0]['distance']:.4f}):")
            print(f"  {search_result['results'][0]['text'][:120]}...")

        # Limpa coleção de teste
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

        print(f"\n{'='*60}")
        print("✓ TODOS OS TESTES PASSARAM")
        print(f"{'='*60}")
        return True

    except Exception as e:
        print(f"\n{'='*60}")
        print("✗ ERRO ao testar embedding:")
        print(f"  {type(e).__name__}: {e}")
        print(f"{'='*60}")
        return False


def main():
    """Executa testes de embedding."""
    print("\n" + "="*60)
    print("TESTE DE EMBEDDINGS COM EMBEDDINGGEMMA")
    print("="*60)
    
    if test_embedding_pipeline():
        print("\n✓ PIPELINE DE EMBEDDINGS FUNCIONA CORRETAMENTE!")
        return 0
    else:
        print("\n✗ TESTE FALHOU")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
