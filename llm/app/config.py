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

# LLM Provider Selection - "ollama" or "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# Ollama Configuration (Local LLM - no rate limits!)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi4-mini")
OLLAMA_TIMEOUT = 300  # seconds (local models can take longer)

# Gemini API Configuration (Cloud LLM - has rate limits)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_TIMEOUT = 120  # seconds

# Tavily API Configuration (for web search fallback)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_SEARCH_DEPTH = "advanced"  # "basic" or "advanced"
TAVILY_MAX_RESULTS = 3

# Relevance threshold - if best match distance is above this, use web search
RELEVANCE_THRESHOLD = 0.8  # Lower distance = more relevant (0.0 = exact match)

TOP_K_RESULTS = 2  # Number of documents to retrieve (reduced for faster inference)
MAX_CONTEXT_LENGTH = 2500  # Maximum characters in context (optimized for speed)
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Use faster model for web search results (since they're less structured)
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

# Dynamic API description based on LLM provider
if LLM_PROVIDER == "ollama":
    API_DESCRIPTION = f"RAG-based Indian Law Assistant using Ollama ({OLLAMA_MODEL}) + ChromaDB"
elif LLM_PROVIDER == "gemini":
    API_DESCRIPTION = f"RAG-based Indian Law Assistant using Gemini ({GEMINI_MODEL}) + ChromaDB"
else:
    API_DESCRIPTION = "RAG-based Indian Law Assistant using ChromaDB"
