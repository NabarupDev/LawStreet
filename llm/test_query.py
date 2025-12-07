"""Test RAG retrieval for IPC Section 420"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.rag import RAGPipeline

rag = RAGPipeline()

queries = [
    "What is IPC Section 420",
    "Section 420 IPC",
    "cheating IPC",
    "dishonestly inducing delivery of property"
]

for query in queries:
    print(f"\nQuery: {query}")
    print("=" * 60)
    
    results = rag.retrieve_documents(query, top_k=10)
    
    for i, doc in enumerate(results, 1):
        print(f"\nDocument {i}:")
        print(f"  Source: {doc['metadata'].get('source', 'N/A')}")
        print(f"  Section Number: {doc['metadata'].get('section_number', 'N/A')}")
        print(f"  Section Title: {doc['metadata'].get('section_title', 'N/A')[:60]}...")
        print(f"  Type: {doc['metadata'].get('type', 'N/A')}")
        print(f"  Chunk: {doc['metadata'].get('chunk_index', 0)}/{doc['metadata'].get('total_chunks', 1)}")
        print(f"  Distance: {doc.get('distance', 'N/A'):.4f}")
        print(f"  Content (first 200 chars): {doc['content'][:200]}...")
    print()
