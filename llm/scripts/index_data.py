r"""
Data Indexing Script: JSON Legal Documents → Embeddings → ChromaDB

PURPOSE:
Converts structured JSON legal documents into semantic embeddings and stores them in a
persistent ChromaDB vector database for efficient retrieval during RAG queries.

CHUNKING STRATEGY:
Documents are split into chunks to:
1. Fit within embedding model's token limit (256 tokens ≈ 800 characters)
2. Improve retrieval precision (retrieve specific passages vs entire sections)
3. Stay within LLM context window when building prompts

CHUNKING CONFIGURATION:
- Chunk size: 800 characters (≈200-250 tokens, leaves margin for safety)
- Chunk overlap: 200 characters (25% overlap to preserve context across boundaries)
- Why overlap? Ensures important information near chunk boundaries isn't lost
- Splitting strategy: Character-based (not word or sentence to keep consistent size)

EXAMPLE CHUNKING:
Original section (1500 chars):
"Section 420: Whoever cheats and thereby dishonestly induces... [1500 characters]"

Chunks created:
- Chunk 0 (chars 0-800): "Section 420: Whoever cheats and thereby..."
- Chunk 1 (chars 600-1400): "...induces the person deceived to deliver..." (starts at 600, overlap)
- Chunk 2 (chars 1200-1500): "...imprisonment or fine or both." (starts at 1200)

STABLE ID GENERATION:
Format: {source}_{section}_{chunk_index}
Examples:
- "ipc_420_0" (IPC Section 420, chunk 0)
- "ipc_420_1" (IPC Section 420, chunk 1)
- "constitution_21_0" (Constitution Article 21, chunk 0)
- "crpc_41_0" (CrPC Section 41, chunk 0)

ID Requirements:
- Must be stable across re-indexing (same document = same ID)
- Must be unique (no collisions)
- Should be human-readable for debugging
- Include chunk index so updates can replace specific chunks

METADATA FIELDS TO STORE (for each chunk):
Required fields:
- source: "Indian Penal Code", "Constitution of India", "Code of Criminal Procedure", etc.
- act: "IPC", "CrPC", "Constitution", "Evidence Act" (abbreviated)
- section: "420", "302", "41" (string, preserve leading zeros)
- article: "21", "14" (for Constitution, alternative to section)
- title: Human-readable section title ("Cheating and dishonestly inducing...")
- type: "ipc", "constitution", "crpc", "evidence", "act"
- chunk_index: 0, 1, 2... (which chunk of this section)
- chunk_total: Total chunks for this section (e.g., 3)

Optional fields:
- chapter: Chapter number/title if available
- chapter_title: Chapter heading
- offense: Type of offense (for IPC)
- punishment: Punishment description (for IPC)
- original_id: Source document ID from JSON (before chunking)
- source_url: URL to official source (if available)
- year_enacted: Year law was enacted
- last_amended: Date of last amendment
- notes: Additional context

WORKFLOW:

1. INITIALIZATION:
   - Create/connect to ChromaDB persistent client at vectorstore/chroma/
   - Delete existing collection if present (clean slate)
   - Create new collection 'indian_law_collection'
   - Load embedding model (must use SAME model as runtime app)
   - Initialize counters and progress tracking

2. LOAD DATA FILES:
   For each JSON file in Data/ directory:
   - ipc.json (Indian Penal Code sections)
   - crpc.json (Criminal Procedure Code)
   - constitution.json (Constitution of India articles)
   - evidence.json (Indian Evidence Act)
   - acts.json (Other acts: HMA, MVA, etc.)
   
   Skip files that don't exist (warn user)
   Validate JSON structure (must be list of dicts)

3. PROCESS EACH DOCUMENT:
   For each legal document in JSON:
   
   a. Extract fields:
      - id, type, section/article, title, content, metadata
      - Validate required fields present
      - Normalize fields (trim whitespace, handle nulls)
   
   b. Create searchable text:
      Format: "Source: {source}\nSection: {section}\nTitle: {title}\n\nContent: {content}"
      This structured format improves retrieval quality
   
   c. Chunk the text:
      If len(text) <= 800 chars:
        - Store as single chunk (chunk_index=0, chunk_total=1)
      Else:
        - Split into overlapping chunks (800 char size, 200 char overlap)
        - Create separate chunk for each with incrementing chunk_index
   
   d. Generate stable IDs:
      For each chunk: "{original_id}_{chunk_index}"
   
   e. Prepare metadata:
      For each chunk, create metadata dict with ALL fields
      Ensure all values are str/int/float (ChromaDB requirement)
      Add chunk_index and chunk_total to metadata

4. BATCH EMBEDDING GENERATION:
   - Collect all chunk texts into a list
   - Generate embeddings in batches (batch_size=100)
   - Use embedding_model.embed_documents(texts)
   - Show progress bar (tqdm) for user feedback
   - Handle OOM by reducing batch size and retrying

5. STORE IN CHROMADB:
   - Add documents in batches (100-500 at a time)
   - collection.add(
       ids=chunk_ids,
       documents=chunk_texts,
       embeddings=chunk_embeddings,
       metadatas=chunk_metadatas
     )
   - Log progress: "Indexed X/Y documents"
   - Handle errors gracefully (log and continue)

6. VERIFICATION:
   - Query collection.count() to verify all chunks stored
   - Test retrieval with sample query
   - Print summary statistics:
     * Total documents processed
     * Total chunks created
     * Documents per source type
     * Average chunks per document
     * Collection size on disk

7. CLEANUP:
   - Close ChromaDB client
   - Free embedding model from memory
   - Print success message

INCREMENTAL UPDATE WORKFLOW:

To add new documents WITHOUT rebuilding entire index:

1. Load existing collection (don't delete)
2. For new JSON file or updated documents:
   - Generate IDs using same scheme
   - Check if ID exists: collection.get(ids=[id])
   - If exists: Use collection.update() to replace
   - If new: Use collection.add() to insert
3. This allows updating specific sections without full reindex

To update existing documents:
1. Generate same ID as original
2. collection.update(ids=[id], documents=[new_text], embeddings=[new_embedding])
3. Metadata will be replaced automatically

FULL REBUILD WORKFLOW:

When to rebuild from scratch:
- Changing embedding model (different dimensions)
- Changing chunking strategy (different chunk sizes)
- Major data schema changes
- Corrupted database

Steps:
1. Backup existing vectorstore/chroma/ directory (optional)
2. Delete collection or entire chroma directory
3. Run this script fresh
4. Verify with test queries
5. Update app to use new collection

ERROR HANDLING:
- Missing JSON file: Log warning, skip file, continue
- Malformed JSON: Log error, skip file
- Missing required fields: Log warning, skip document
- Embedding failure: Retry once, then skip document
- ChromaDB write failure: Retry batch, then fail script
- OOM during embedding: Reduce batch size, retry

LOGGING OUTPUT:
============================================================
Legal AI - Data Indexing Script
============================================================

1. Initializing ChromaDB at: E:\LawStreet\vectorstore\chroma
   Created collection: indian_law_collection

2. Loading embedding model...
   Model loaded: sentence-transformers/all-MiniLM-L6-v2

3. Loading and indexing legal documents...

   Processing ipc...
     Loaded 511 documents
     Preparing ipc: 100%|████████| 511/511
     Generated 1247 chunks (avg 2.4 chunks/doc)
     Generating embeddings: 100%|████████| 1247/1247
     ✓ Indexed 1247 chunks from ipc

   Processing constitution...
     [similar output]

============================================================
Indexing Complete!
Total documents indexed: 3542 chunks from 1456 documents
Collection: indian_law_collection
Location: E:\LawStreet\vectorstore\chroma
============================================================

SAME EMBEDDING FUNCTION REQUIREMENT:
CRITICAL: This script must use the EXACT SAME embedding model and configuration
as the runtime application (app/embed.py). Otherwise, query embeddings won't match
document embeddings and retrieval will fail.

Ensure both use:
- Same model: sentence-transformers/all-MiniLM-L6-v2
- Same normalization: L2 normalized
- Same tokenization: Default tokenizer settings
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings
from tqdm import tqdm

from app.embed import get_embedding_model
from app.config import (
    CHROMA_DIR,
    CHROMA_COLLECTION_NAME,
    DATA_FILES
)


def load_json_file(filepath):
    """Load and return JSON data from file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_document_text(item: dict) -> str:
    """
    Create a searchable text representation of a legal document
    
    Args:
        item: Dictionary containing legal document data
        
    Returns:
        Formatted text string for embedding
    """
    parts = []
    
    doc_type = item.get('type', '')
    source = item.get('metadata', {}).get('source', '')
    
    if doc_type == 'ipc':
        act_abbrev = "IPC"
    elif doc_type == 'crpc':
        act_abbrev = "CrPC"
    elif doc_type == 'constitution':
        act_abbrev = "Constitution"
    elif doc_type == 'evidence':
        act_abbrev = "Evidence Act"
    elif doc_type == 'cpc':
        act_abbrev = "CPC"
    elif doc_type == 'mva':
        act_abbrev = "MVA"
    elif doc_type == 'hma':
        act_abbrev = "HMA"
    elif doc_type == 'nia':
        act_abbrev = "NIA"
    elif doc_type == 'ida':
        act_abbrev = "IDA"
    else:
        act_abbrev = doc_type.upper() if doc_type else ""
    
    if source:
        parts.append(f"Source: {source}")
    
    if 'section' in item:
        if act_abbrev:
            parts.append(f"{act_abbrev} Section {item['section']}")
        else:
            parts.append(f"Section {item['section']}")
    elif 'article' in item:
        if act_abbrev:
            parts.append(f"{act_abbrev} Article {item['article']}")
        else:
            parts.append(f"Article {item['article']}")
    
    if 'section_title' in item and item['section_title']:
        parts.append(f"Title: {item['section_title']}")
    elif 'title' in item and item['title']:
        parts.append(f"Title: {item['title']}")
    
    if 'chapter_title' in item and item['chapter_title']:
        parts.append(f"Chapter: {item['chapter_title']}")
    
    if 'content' in item and item['content']:
        parts.append(f"Content: {item['content']}")
    
    if 'offense' in item and item['offense']:
        parts.append(f"Offense: {item['offense']}")
    
    if 'punishment' in item and item['punishment']:
        parts.append(f"Punishment: {item['punishment']}")
    
    return "\n".join(parts)


def index_data_to_chroma():
    """
    Load all legal data from JSON files and index into ChromaDB
    """
    print("=" * 60)
    print("Legal AI - Data Indexing Script")
    print("=" * 60)
    
    print(f"\n1. Initializing ChromaDB at: {CHROMA_DIR}")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False)
    )
    
    try:
        client.delete_collection(name=CHROMA_COLLECTION_NAME)
        print(f"   Deleted existing collection: {CHROMA_COLLECTION_NAME}")
    except:
        pass
    
    collection = client.create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"description": "Indian Law Documents"}
    )
    print(f"   Created collection: {CHROMA_COLLECTION_NAME}")
    
    print("\n2. Loading embedding model...")
    embedding_model = get_embedding_model()
    print(f"   Model loaded: {embedding_model.model_name}")
    
    print("\n3. Loading and indexing legal documents...")
    
    total_documents = 0
    
    for data_type, filepath in DATA_FILES.items():
        if not filepath.exists():
            print(f"\n   ⚠ Skipping {data_type}: File not found at {filepath}")
            continue
        
        print(f"\n   Processing {data_type}...")
        
        try:
            data = load_json_file(filepath)
            print(f"     Loaded {len(data)} documents")
        except Exception as e:
            print(f"     ✗ Error loading file: {e}")
            continue
        
        if not data:
            print(f"     ⚠ No data found in file")
            continue
        
        ids = []
        documents = []
        metadatas = []
        
        for idx, item in enumerate(tqdm(data, desc=f"     Preparing {data_type}", unit="doc")):
            base_id = item.get('id', f"{data_type}_{idx}")
            doc_id = f"{base_id}_{idx}" if base_id in ids else base_id
            ids.append(doc_id)
            
            doc_text = create_document_text(item)
            documents.append(doc_text)
            
            metadata = item.get('metadata', {})
            if 'type' not in metadata:
                metadata['type'] = item.get('type', data_type)
            clean_metadata = {}
            for key, value in metadata.items():
                if value is not None:
                    if isinstance(value, (str, int, float)):
                        clean_metadata[key] = value
                    else:
                        clean_metadata[key] = str(value)
            metadatas.append(clean_metadata)
        
        print(f"     Generating embeddings for {len(documents)} documents...")
        embeddings = embedding_model.embed_documents(documents)
        
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            end_idx = min(i + batch_size, len(ids))
            collection.add(
                ids=ids[i:end_idx],
                documents=documents[i:end_idx],
                embeddings=embeddings[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )
        
        print(f"     ✓ Indexed {len(ids)} documents from {data_type}")
        total_documents += len(ids)
    
    print("\n" + "=" * 60)
    print(f"Indexing Complete!")
    print(f"Total documents indexed: {total_documents}")
    print(f"Collection: {CHROMA_COLLECTION_NAME}")
    print(f"Location: {CHROMA_DIR}")
    print("=" * 60)
    
    print("\nVerifying collection...")
    count = collection.count()
    print(f"Documents in collection: {count}")
    
    if count > 0:
        print("\n✓ Success! The vector database is ready.")
        print("  You can now run the API server with: python -m app.main")
    else:
        print("\n✗ Warning: No documents were indexed.")


if __name__ == "__main__":
    index_data_to_chroma()
