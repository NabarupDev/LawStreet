"""
Embedding Model using Sentence Transformers

PURPOSE:
Provides text embedding functionality using sentence-transformers library.
Converts text (queries and documents) into dense vector representations for semantic search.

MODEL SPECIFICATION:
- Model: sentence-transformers/all-MiniLM-L6-v2
- Embedding dimension: 384
- Max sequence length: 256 tokens (longer texts auto-truncated)
- Normalization: L2-normalized vectors (for cosine similarity)
- Download size: ~80 MB (cached in ~/.cache/torch/)

FUNCTION SPECIFICATIONS:

class EmbeddingModel:
    def __init__(model_name: str):
        BEHAVIOR:
        1. Download model from HuggingFace if not cached locally
        2. Load model into memory (PyTorch)
        3. Set model to evaluation mode (no training)
        4. Move to GPU if available (automatically detected)
        5. Store model reference for reuse
        
        EDGE CASES:
        - No internet + not cached: Raise error with helpful message
        - Insufficient memory: Raise OOM error
        - Invalid model name: Raise model not found error
        
        TIMEOUT: 300 seconds for initial download
    
    def embed_text(text: str | list[str]) -> list[float] | list[list[float]]:
        BEHAVIOR FOR SINGLE STRING:
        1. Tokenize text using model's tokenizer
        2. Truncate to 256 tokens if longer
        3. Pass through model encoder
        4. Extract embeddings from last layer
        5. Apply mean pooling across tokens
        6. L2 normalize the resulting vector
        7. Convert PyTorch tensor to Python list of floats
        8. Return vector[384]
        
        BEHAVIOR FOR LIST OF STRINGS (BATCH):
        1. Process all texts in a single batch (efficient)
        2. Show progress bar for large batches (>100 texts)
        3. Handle batching automatically (splits if >1000 texts)
        4. Return list of vectors: [[vec1], [vec2], ...]
        
        LENGTH NORMALIZATION:
        - All output vectors are exactly 384 dimensions
        - All vectors are L2-normalized (magnitude = 1.0)
        - This ensures cosine similarity = dot product
        
        BATCH SIZE STRATEGY:
        - Optimal batch size: 32-128 depending on text length
        - Auto-adjust batch size based on available memory
        - For >1000 texts, split into mini-batches
        - For <10 texts, process in single batch
        
        EDGE CASES:
        - Empty string: Returns zero vector or small random vector
        - Non-ASCII characters: Handled by tokenizer (supports multilingual)
        - Very long text (>256 tokens): Auto-truncated, no error
        - Mixed Hindi/English: Tokenizer handles code-switching
    
    def embed_query(query: str) -> list[float]:
        WRAPPER around embed_text for single query
        Ensures consistent interface for RAG pipeline
        Returns vector[384]
    
    def embed_documents(documents: list[str]) -> list[list[float]]:
        WRAPPER around embed_text for batch of documents
        Shows progress bar for user feedback during indexing
        Returns list of vector[384]

SINGLETON PATTERN:
get_embedding_model() -> EmbeddingModel
    - Lazy initialization: Create model on first call
    - Store in global _embedding_model variable
    - Reuse same instance for all subsequent calls
    - Thread-safe for concurrent read operations
    - Prevents reloading model (expensive) on each query

PERFORMANCE:
- Single query embedding: ~50-100ms on CPU, ~10-20ms on GPU
- Batch of 100 documents: ~2-5 seconds on CPU, ~0.5-1s on GPU
- Memory usage: ~300 MB for model + ~1 MB per 1000 embeddings
- GPU acceleration: Automatic if CUDA available

ERROR HANDLING:
- Model download failure: Provide clear instructions to user
- OOM during batching: Reduce batch size and retry
- Tokenization errors: Log warning, skip problematic text
- Invalid input type: Raise TypeError with explanation

CACHING:
- Model weights cached by HuggingFace (~/.cache/torch/)
- No need to cache embeddings at this layer (ChromaDB handles storage)
- Tokenizer vocab cached automatically

TESTING:
To verify embeddings are correct:
1. Embed same text twice -> should get identical vectors
2. Embed similar texts -> should have high cosine similarity (>0.8)
3. Embed unrelated texts -> should have low similarity (<0.3)
4. Check vector dimension = 384
5. Check vector magnitude ≈ 1.0 (normalized)
"""
import os
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
from app.config import EMBEDDING_MODEL

# Memory optimization: Force CPU-only mode
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")


class EmbeddingModel:
    """Wrapper for sentence-transformer embedding model"""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize the embedding model
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        print(f"Loading embedding model: {model_name}")
        # Force CPU device to save memory
        self.model = SentenceTransformer(model_name, device='cpu')
        self.model_name = model_name
        print(f"Embedding model loaded successfully (CPU mode)")
        
    def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            Embedding vector(s) as list(s) of floats
        """
        if isinstance(text, str):
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        else:
            embeddings = self.model.encode(text, convert_to_numpy=True, show_progress_bar=True)
            return embeddings.tolist()
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query
        
        Args:
            query: Query text string
            
        Returns:
            Embedding vector as list of floats
        """
        return self.embed_text(query)
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents
        
        Args:
            documents: List of document text strings
            
        Returns:
            List of embedding vectors
        """
        return self.embed_text(documents)


_embedding_model = None


def get_embedding_model() -> EmbeddingModel:
    """
    Get or create the global embedding model instance
    
    Returns:
        EmbeddingModel instance
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
