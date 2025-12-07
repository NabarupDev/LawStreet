"""Check if IPC Section 420 is in ChromaDB"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import chromadb
from chromadb.config import Settings
from app.config import CHROMA_DIR, CHROMA_COLLECTION_NAME

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR),
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_collection(name=CHROMA_COLLECTION_NAME)

results = collection.get(
    where={"$and": [
        {"type": "ipc"},
        {"section_number": "420"}
    ]},
    include=["documents", "metadatas"]
)

print(f"Found {len(results['documents'])} documents for IPC Section 420\n")

if results['documents']:
    for i, doc in enumerate(results['documents'][:2]):
        print(f"Document {i+1}:")
        print(f"  ID: {results['ids'][i]}")
        print(f"  Content: {doc[:300]}...")
        print(f"  Metadata: {results['metadatas'][i]}")
        print()
else:
    print("No documents found!")
    
print("\nChecking all documents in database...")
all_docs = collection.get(
    limit=10,
    include=["metadatas"]
)
print(f"Total documents in collection: {collection.count()}")
print(f"\nSample metadata from first 5 documents:")
for i, meta in enumerate(all_docs['metadatas'][:5], 1):
    print(f"\n{i}. ID: {all_docs['ids'][i-1]}")
    print(f"   Type: {meta.get('type')}")
    print(f"   Section Number: {meta.get('section_number')}")
    print(f"   Section Title: {meta.get('section_title', '')[:60]}...")
    print(f"   Chunk: {meta.get('chunk_index')}/{meta.get('total_chunks')}")
