"""Configuration settings for the backend."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
PROMPTS_FILE = os.getenv("PROMPTS_FILE", str(BASE_DIR / "prompts.yaml"))

# Database URLs
POSTGRES_URL = os.getenv("POSTGRES_URL")
MONGO_HOST = os.getenv("MONGO_HOST", "ec-project-mongo")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DB = os.getenv("MONGO_DB", "ec_project")
CHROMA_HOST = os.getenv("CHROMA_HOST", "ec-project-chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# API Settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))

# RAG tuning defaults
SEARCH_DISTANCE_THRESHOLD = float(os.getenv("SEARCH_DISTANCE_THRESHOLD", "0.8"))
MIN_CHUNK_LENGTH = int(os.getenv("MIN_CHUNK_LENGTH", "40"))
RAG_COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "steam_reviews")

# Other
STEAM_APP_ID = os.getenv("STEAM_APP_ID")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
SESSION_SECRET = os.getenv("SESSION_SECRET")