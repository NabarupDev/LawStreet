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

# LLM Provider Selection: "ollama", "gemini", or "middleware"
# Use "middleware" for Open LLM Middleware with multi-provider support
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "middleware").lower()

# ==================== Open LLM Middleware Configuration ====================
# Multi-provider LLM middleware with failover, retry logic, and WebSocket support
# Live server: https://open-llm-mslh.onrender.com

LLM_MIDDLEWARE_URL = os.getenv("LLM_MIDDLEWARE_URL", "https://open-llm-mslh.onrender.com")
LLM_MIDDLEWARE_SECRET = os.getenv("LLM_MIDDLEWARE_SECRET", "")

# Middleware provider: "openai", "google", "cerebras", "groq"
# - openai: GPT-4o (best quality)
# - google: Gemini 2.5 Flash (default, 1M context window)
# - cerebras: Llama 3.3 70B (fastest inference, 30 req/min limit)
# - groq: Llama 3.3 70B Versatile (fast inference)
LLM_MIDDLEWARE_PROVIDER = os.getenv("LLM_MIDDLEWARE_PROVIDER", "google")

# Optional: Specify model (leave empty for provider default)
LLM_MIDDLEWARE_MODEL = os.getenv("LLM_MIDDLEWARE_MODEL", "")

# Request timeout in seconds
LLM_MIDDLEWARE_TIMEOUT = int(os.getenv("LLM_MIDDLEWARE_TIMEOUT", "120"))

# Maximum tokens in response
LLM_MIDDLEWARE_MAX_TOKENS = int(os.getenv("LLM_MIDDLEWARE_MAX_TOKENS", "2048"))

# Use WebSocket for faster bidirectional communication (experimental)
LLM_MIDDLEWARE_USE_WEBSOCKET = os.getenv("LLM_MIDDLEWARE_USE_WEBSOCKET", "false").lower() == "true"

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
elif LLM_PROVIDER == "middleware":
    API_DESCRIPTION = f"RAG-based Indian Law Assistant using Open LLM Middleware ({LLM_MIDDLEWARE_PROVIDER}) + ChromaDB"
else:
    API_DESCRIPTION = "RAG-based Indian Law Assistant using ChromaDB"
