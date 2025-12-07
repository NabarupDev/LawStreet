"""
Legal AI - RAG System for Indian Law
Package initialization
"""

__version__ = "1.0.0"
__title__ = "Legal AI Assistant"
__description__ = "RAG-based Indian Law Assistant using Google Gemini + ChromaDB"

from app.config import *
from app.embed import get_embedding_model
from app.rag import get_rag_pipeline
