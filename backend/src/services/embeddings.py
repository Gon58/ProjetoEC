"""
Embedding generation service using Ollama.
"""

from typing import List

import ollama

from ..core.config import EMBEDDING_MODEL, OLLAMA_BASE_URL


def get_ollama_client() -> ollama.Client:
    """Creates an Ollama client configured with the current host."""
    return ollama.Client(host=OLLAMA_BASE_URL)


def ensure_model(model: str | None = None) -> bool:
    """
    Ensures that a model is available in Ollama, pulling it if necessary.
    """
    model = model or EMBEDDING_MODEL
    client = get_ollama_client()

    try:
        response = client.list()
        models_list = response.get("models", [])

        available_models = set()
        for model_info in models_list:
            model_name = model_info.get("model", model_info.get("name", ""))
            if model_name:
                available_models.add(model_name)
                available_models.add(model_name.split(":")[0])

        if model in available_models:
            return True

        print(f"Model '{model}' not found. Pulling...")
        client.pull(model)
        print(f"Model '{model}' successfully downloaded.")
        return True

    except Exception as e:
        print(f"Error checking/downloading model '{model}': {e}")
        raise


def embed_text(text: str) -> List[float]:
    """Generates embedding for a single text."""
    ensure_model()
    client = get_ollama_client()
    response = client.embed(model=EMBEDDING_MODEL, input=text)
    return response["embeddings"][0]


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generates embeddings for multiple texts."""
    if not texts:
        return []

    ensure_model()
    client = get_ollama_client()
    response = client.embed(model=EMBEDDING_MODEL, input=texts)
    return response["embeddings"]