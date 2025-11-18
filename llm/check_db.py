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
        {"section": "420"}
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
    
print("\nChecking all IPC sections in database...")
all_ipc = collection.get(
    where={"type": "ipc"},
    limit=10,
    include=["metadatas"]
)
print(f"Total IPC documents: {collection.count()}")
print(f"Sample IPC metadata:")
for meta in all_ipc['metadatas'][:5]:
    print(f"  Section: {meta.get('section')}, Type: {type(meta.get('section'))}")
