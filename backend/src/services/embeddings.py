"""
Embedding generation service using Ollama.
"""

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import List

import ollama

from ..core.config import EMBEDDING_MODEL, OLLAMA_BASE_URL, OLLAMA_TIMEOUT_SECONDS


class EmbeddingError(RuntimeError):
    """Base class for embedding-related errors."""


class EmbeddingProviderUnavailableError(EmbeddingError):
    """Raised when the embedding provider is unavailable or times out."""


_CHECKED_MODELS: set[str] = set()


def _run_with_timeout(func, *args, timeout: float = OLLAMA_TIMEOUT_SECONDS, **kwargs):
    """Runs a blocking Ollama call with timeout protection."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except FutureTimeoutError as exc:
            raise EmbeddingProviderUnavailableError(
                f"Embedding request exceeded timeout of {timeout} seconds"
            ) from exc


def get_ollama_client() -> ollama.Client:
    """Creates an Ollama client configured with the current host."""
    return ollama.Client(host=OLLAMA_BASE_URL)


def ensure_model(model: str | None = None) -> bool:
    """
    Ensures that a model is available in Ollama, pulling it if necessary.
    """
    model = model or EMBEDDING_MODEL
    if model in _CHECKED_MODELS:
        return True

    client = get_ollama_client()

    try:
        response = _run_with_timeout(client.list, timeout=OLLAMA_TIMEOUT_SECONDS)
        models_list = response.get("models", [])

        available_models = set()
        for model_info in models_list:
            model_name = model_info.get("model", model_info.get("name", ""))
            if model_name:
                available_models.add(model_name)
                available_models.add(model_name.split(":")[0])

        if model in available_models:
            _CHECKED_MODELS.add(model)
            return True

        print(f"Model '{model}' not found. Pulling...")
        _run_with_timeout(client.pull, model, timeout=OLLAMA_TIMEOUT_SECONDS)
        print(f"Model '{model}' successfully downloaded.")
        _CHECKED_MODELS.add(model)
        return True

    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingProviderUnavailableError(
            f"Error checking/downloading model '{model}': {exc}"
        ) from exc


def embed_text(text: str) -> List[float]:
    """Generates embedding for a single text."""
    ensure_model()
    client = get_ollama_client()
    try:
        response = _run_with_timeout(
            client.embed,
            model=EMBEDDING_MODEL,
            input=text,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        embeddings = response.get("embeddings") or []
        if not embeddings:
            raise EmbeddingProviderUnavailableError("Embedding provider returned no vectors")
        return embeddings[0]
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingProviderUnavailableError(
            f"Failed to generate embedding for query text: {exc}"
        ) from exc


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generates embeddings for multiple texts."""
    if not texts:
        return []

    ensure_model()
    client = get_ollama_client()
    try:
        response = _run_with_timeout(
            client.embed,
            model=EMBEDDING_MODEL,
            input=texts,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        embeddings = response.get("embeddings") or []
        if not embeddings:
            raise EmbeddingProviderUnavailableError(
                "Embedding provider returned no vectors for chunk batch"
            )
        return embeddings
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingProviderUnavailableError(
            f"Failed to generate embeddings for chunk batch: {exc}"
        ) from exc