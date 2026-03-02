"""
Serviço de geração de embeddings usando Ollama.

Fornece funções para gerar embeddings de textos utilizando
modelos disponíveis no Ollama.
"""

import os
from typing import List

import ollama


def get_ollama_host() -> str:
    """Obtém o endereço do servidor Ollama a partir das variáveis de ambiente."""
    return os.getenv("OLLAMA_HOST", "http://localhost:11434")


def get_ollama_client() -> ollama.Client:
    """Cria um cliente Ollama configurado com o host atual."""
    return ollama.Client(host=get_ollama_host())


def ensure_model(model: str) -> bool:
    """
    Garante que um modelo está disponível no Ollama, fazendo pull se necessário.

    Args:
        model: Nome do modelo a verificar/baixar.

    Returns:
        True se o modelo está disponível, False se falhou.

    Raises:
        Exception: Se não conseguir verificar ou baixar o modelo.
    """
    client = get_ollama_client()
    
    try:
        # Lista modelos disponíveis
        response = client.list()
        models_list = response.get("models", [])
        
        # Extrai nomes dos modelos (remove tags :latest)
        available_models = set()
        for model_info in models_list:
            # Tenta pegar o nome do modelo
            model_name = model_info.get("model", model_info.get("name", ""))
            if model_name:
                # Remove :latest ou outras tags
                base_name = model_name.split(":")[0]
                available_models.add(base_name)
                available_models.add(model_name)
        
        # Verifica se modelo já existe
        if model in available_models:
            return True
        
        # Modelo não existe - faz pull
        print(f"Modelo '{model}' não encontrado. Fazendo pull...")
        client.pull(model)
        print(f"Modelo '{model}' baixado com sucesso.")
        return True
        
    except Exception as e:
        print(f"Erro ao verificar/baixar modelo '{model}': {e}")
        raise


def embed_text(text: str) -> List[float]:
    """
    Gera embedding para um texto único usando embeddinggemma.

    Args:
        text: O texto para gerar embedding.

    Returns:
        Lista de floats representando o vetor de embedding.

    Raises:
        ollama.ResponseError: Se a geração de embedding falhar.
    """
    ensure_model("embeddinggemma")
    client = get_ollama_client()
    response = client.embed(model="embeddinggemma", input=text)
    return response["embeddings"][0]


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Gera embeddings para múltiplos textos usando embeddinggemma.

    Args:
        texts: Lista de textos para gerar embeddings.

    Returns:
        Lista de vetores de embedding.

    Raises:
        ollama.ResponseError: Se a geração de embeddings falhar.
    """
    if not texts:
        return []

    ensure_model("embeddinggemma")
    client = get_ollama_client()
    response = client.embed(model="embeddinggemma", input=texts)
    return response["embeddings"]
