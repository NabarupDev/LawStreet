"""
Configuration settings for Legal AI RAG system
"""
import os
from pathlib import Path
from dotenv import load_dotenv

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

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi4-mini")
OLLAMA_TIMEOUT = 300

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_TIMEOUT = 120  # seconds

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_SEARCH_DEPTH = "advanced"  # "basic" or "advanced"
TAVILY_MAX_RESULTS = 3

RELEVANCE_THRESHOLD = 0.8 

TOP_K_RESULTS = 2  
MAX_CONTEXT_LENGTH = 2500  
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

USE_GEMINI_FOR_WEB_SEARCH = os.getenv("USE_GEMINI_FOR_WEB_SEARCH", "true").lower() == "true"

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

if LLM_PROVIDER == "ollama":
    API_DESCRIPTION = f"RAG-based Indian Law Assistant using Ollama ({OLLAMA_MODEL}) + ChromaDB"
elif LLM_PROVIDER == "gemini":
    API_DESCRIPTION = f"RAG-based Indian Law Assistant using Gemini ({GEMINI_MODEL}) + ChromaDB"
else:
    API_DESCRIPTION = "RAG-based Indian Law Assistant using ChromaDB"
