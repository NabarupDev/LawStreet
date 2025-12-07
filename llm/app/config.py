"""
Configuration settings for Legal AI RAG system
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "Data"
MODEL_DIR = BASE_DIR / "model"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
CHROMA_DIR = VECTORSTORE_DIR / "chroma"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

CHROMA_COLLECTION_NAME = "indian_law_collection"
CHROMA_DISTANCE_METRIC = "cosine"

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_TIMEOUT = 120  # seconds

TOP_K_RESULTS = 5  # Number of documents to retrieve (reduced for focused context)
MAX_CONTEXT_LENGTH = 8000  # Maximum characters in context (Gemini can handle more)
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

PROMPT_TEMPLATE_PATH = MODEL_DIR / "prompt_template.txt"

DATA_FILES = {
    "ipc": DATA_DIR / "raw" / "ipc_dataset.json",
    "crpc": DATA_DIR / "raw" / "crpc_dataset.json",
    "cpc": DATA_DIR / "raw" / "cpc_dataset.json",
    "evidence": DATA_DIR / "raw" / "evidence_act_dataset.json"
}

API_HOST = "0.0.0.0"
API_PORT = 8000
API_TITLE = "Legal AI Assistant"
API_VERSION = "1.0.0"
API_DESCRIPTION = "RAG-based Indian Law Assistant using Google Gemini + ChromaDB"
