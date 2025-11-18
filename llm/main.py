"""
Alternative entry point for Legal AI application
Run with: python main.py
"""
from app.main import app
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Legal AI Assistant - Indian Law RAG System")
    print("=" * 60)
    print("\nStarting server...")
    print("API will be available at: http://localhost:8000")
    print("API Documentation at: http://localhost:8000/docs")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
