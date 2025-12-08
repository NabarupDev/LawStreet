"""
FastAPI Backend for Legal AI RAG System

PURPOSE:
This file implements the main API server that exposes endpoints for querying Indian legal documents
using a Retrieval-Augmented Generation (RAG) approach with Llama 3.3.

INITIALIZATION BEHAVIOR:
- On server startup (startup_event), initialize the embedding model ONCE (singleton pattern)
- Load the ChromaDB collection ONCE and keep it in memory
- Verify that the collection exists and contains documents
- If initialization fails, log error and prevent server from starting

API ENDPOINTS:

1. POST /ask
   INPUT: JSON { "query": "string" }
   - query: user's legal question (min 1 character, max 2000 characters)
   
   OUTPUT: JSON {
     "answer": "string",           // Generated answer from Llama 3.3
     "query": "string",            // Echo of original query
     "num_retrieved_docs": int,    // Number of documents retrieved from ChromaDB
     "sources": [                   // Top 3-5 source documents used
       {
         "source": "string",       // Act name (IPC, CrPC, Constitution, etc.)
         "section": "string",      // Section/Article number
         "distance": float         // Similarity score (lower = more relevant)
       }
     ]
   }
   
   PROCESSING FLOW:
   1. Validate request (check query not empty, reasonable length)
   2. Pass query to RAG pipeline
   3. RAG pipeline returns structured result
   4. Format and return response
   5. If any step fails, return HTTP 500 with error details

2. GET /health
   Returns status of all system components:
   - ChromaDB collection status and document count
   - Embedding model status
   - Ollama connectivity (optional check)
   
3. GET /
   Returns API information and available endpoints

ERROR HANDLING:
- 422 Unprocessable Entity: Invalid request format or validation errors
- 500 Internal Server Error: RAG pipeline failures, model errors, database errors
- 503 Service Unavailable: Ollama not reachable (should retry)
- Log all errors with full stack trace for debugging

TIMEOUT CONFIGURATION:
- API request timeout: 120 seconds (allow time for LLM generation)
- Ollama call timeout: 90 seconds (configurable in config.py)
- ChromaDB query timeout: 10 seconds
- If Ollama times out, return partial response with error message

CONCURRENCY:
- FastAPI handles concurrent requests automatically
- Embedding model is thread-safe (sentence-transformers)
- ChromaDB client is thread-safe for reads
- Use connection pooling for Ollama if available

CORS CONFIGURATION:
- Allow all origins (for development)
- For production, restrict to specific domains
- Allow credentials for authenticated requests (future)

MIDDLEWARE:
- CORS middleware for cross-origin requests
- Request logging middleware (optional)
- Error handling middleware to catch unhandled exceptions

STARTUP CHECKS:
- Verify ChromaDB directory exists
- Verify collection has documents (count > 0)
- Verify embedding model can be loaded
- Log all initialization steps with timestamps

GRACEFUL SHUTDOWN:
- On SIGTERM/SIGINT, complete in-flight requests
- Close ChromaDB client connections
- Log shutdown event
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn

from app.config import API_HOST, API_PORT, API_TITLE, API_VERSION, API_DESCRIPTION
from app.rag import get_rag_pipeline


class QueryRequest(BaseModel):
    """Request model for ask endpoint"""
    query: str = Field(..., description="Legal question to ask", min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the punishment for theft under IPC?"
            }
        }


class SourceInfo(BaseModel):
    """Information about a source document"""
    source: str
    section: str
    type: Optional[str] = None
    url: Optional[str] = None
    distance: float
    
    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict) and 'section' in obj:
            obj['section'] = str(obj['section'])
        return super().model_validate(obj)


class QueryResponse(BaseModel):
    """Response model for ask endpoint"""
    answer: str = Field(..., description="Generated answer from the legal assistant")
    query: str = Field(..., description="Original query")
    num_retrieved_docs: int = Field(..., description="Number of documents retrieved")
    used_web_search: bool = Field(default=False, description="Whether web search was used as fallback")
    sources: List[SourceInfo] = Field(..., description="Top source documents used")


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize RAG pipeline on startup"""
    try:
        get_rag_pipeline()
        print("✓ RAG Pipeline initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing RAG Pipeline: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "description": API_DESCRIPTION,
        "endpoints": {
            "/ask": "POST - Ask a legal question",
            "/health": "GET - Check API health status",
            "/docs": "GET - API documentation (Swagger UI)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        pipeline = get_rag_pipeline()
        
        count = pipeline.collection.count()
        
        return {
            "status": "healthy",
            "collection": pipeline.collection.name,
            "document_count": count,
            "embedding_model": pipeline.embedding_model.model_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    Ask a legal question and get an answer using RAG
    
    Args:
        request: QueryRequest with the question
        
    Returns:
        QueryResponse with answer and metadata
    """
    try:
        pipeline = get_rag_pipeline()
        
        result = pipeline.ask(request.query)
        
        return QueryResponse(
            answer=result["answer"],
            query=result["query"],
            num_retrieved_docs=result["num_retrieved_docs"],
            sources=[SourceInfo(**source) for source in result["sources"]]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


if __name__ == "__main__":
    """Run the API server"""
    print(f"Starting {API_TITLE} v{API_VERSION}")
    print(f"Server will be available at http://{API_HOST}:{API_PORT}")
    print(f"API documentation at http://{API_HOST}:{API_PORT}/docs")
    
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )
