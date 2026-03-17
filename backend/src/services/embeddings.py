"""
Serviço de geração de embeddings usando Ollama.

Fornece funções para gerar embeddings de textos utilizando
modelos disponíveis no Ollama.
"""

import os
import shutil
import subprocess
import time
from typing import List

import ollama

OLLAMA_AUTOSTART = os.getenv("OLLAMA_AUTOSTART", "1") == "1"
OLLAMA_DOCKER_SERVICE = os.getenv("OLLAMA_DOCKER_SERVICE", "ec-project-ollama")
OLLAMA_START_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_START_TIMEOUT_SECONDS", "30"))


def get_ollama_host() -> str:
    """Obtém o endereço do servidor Ollama a partir das variáveis de ambiente."""
    return os.getenv("OLLAMA_HOST", "http://localhost:11434")


def get_ollama_client() -> ollama.Client:
    """Cria um cliente Ollama configurado com o host atual."""
    return ollama.Client(host=get_ollama_host())


def _start_ollama_service_if_possible() -> bool:
    """
    Tenta iniciar o servico Ollama via Docker Compose, quando disponivel.

    Returns:
        True se foi possivel disparar tentativa de start, False caso contrario.
    """
    if not OLLAMA_AUTOSTART:
        return False

    docker_path = shutil.which("docker")
    if not docker_path:
        return False

    try:
        subprocess.run(
            [docker_path, "compose", "up", "-d", OLLAMA_DOCKER_SERVICE],
            check=False,
            capture_output=True,
            text=True,
        )
        return True
    except Exception:
        return False


def ensure_ollama_available() -> None:
    """
    Garante que o host Ollama esta acessivel antes de usar modelos.

    Estrategia:
    1. Testa ligacao imediata com client.list().
    2. Se falhar, tenta iniciar automaticamente o servico via Docker Compose.
    3. Faz retries por uma janela curta de tempo.

    Raises:
        RuntimeError: Se Ollama continuar indisponivel apos retries.
    """
    client = get_ollama_client()

    try:
        client.list()
        return
    except Exception:
        pass

    _start_ollama_service_if_possible()

    deadline = time.time() + OLLAMA_START_TIMEOUT_SECONDS
    while time.time() < deadline:
        try:
            client = get_ollama_client()
            client.list()
            return
        except Exception:
            time.sleep(1)

    raise RuntimeError(
        "Ollama is unavailable. Attempted auto-start via Docker Compose but could not connect. "
        "Ensure the service is running and OLLAMA_HOST is correct."
    )


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
    ensure_ollama_available()
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
