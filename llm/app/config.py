"""
Configuration settings for Legal AI RAG system
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "Data"
MODEL_DIR = BASE_DIR / "model"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
CHROMA_DIR = VECTORSTORE_DIR / "chroma"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

CHROMA_COLLECTION_NAME = "indian_law_collection"
CHROMA_DISTANCE_METRIC = "cosine"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:1b"
OLLAMA_TIMEOUT = 120  # seconds

TOP_K_RESULTS = 10  # Number of documents to retrieve
MAX_CONTEXT_LENGTH = 4000  # Maximum characters in context
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

PROMPT_TEMPLATE_PATH = MODEL_DIR / "prompt_template.txt"

DATA_FILES = {
    "ipc": DATA_DIR / "ipc.json",
    "crpc": DATA_DIR / "crpc.json",
    "constitution": DATA_DIR / "constitution.json",
    "evidence": DATA_DIR / "evidence.json",
    "acts": DATA_DIR / "acts.json"
}

API_HOST = "0.0.0.0"
API_PORT = 8000
API_TITLE = "Legal AI Assistant"
API_VERSION = "1.0.0"
API_DESCRIPTION = "RAG-based Indian Law Assistant using Ollama + Llama 3.2:1b + ChromaDB"
