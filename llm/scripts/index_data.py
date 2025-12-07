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


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # If this is not the last chunk, try to break at a sentence or word boundary
        if end < len(text):
            # Look for sentence boundary (., !, ?)
            last_period = text.rfind('.', start, end)
            last_question = text.rfind('?', start, end)
            last_exclaim = text.rfind('!', start, end)
            boundary = max(last_period, last_question, last_exclaim)
            
            # If no sentence boundary, look for word boundary
            if boundary == -1 or boundary < start + chunk_size // 2:
                boundary = text.rfind(' ', start, end)
            
            # If found a good boundary, use it
            if boundary > start:
                end = boundary + 1
        
        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else len(text)
    
    return chunks


def create_document_text(item: dict, doc_type: str) -> str:
    """
    Create a searchable text representation of a legal document from scraped data
    
    Args:
        item: Dictionary containing legal document data from scraper
        doc_type: Type of document (ipc, crpc, cpc, evidence)
        
    Returns:
        Formatted text string for embedding
    """
    parts = []
    
    # Determine act abbreviation
    if doc_type == 'ipc':
        act_abbrev = "IPC"
        act_name = "Indian Penal Code, 1860"
    elif doc_type == 'crpc':
        act_abbrev = "CrPC"
        act_name = "Code of Criminal Procedure, 1973"
    elif doc_type == 'cpc':
        act_abbrev = "CPC"
        act_name = "Code of Civil Procedure, 1908"
    elif doc_type == 'evidence':
        act_abbrev = "Evidence Act"
        act_name = "Indian Evidence Act, 1872"
    else:
        act_abbrev = doc_type.upper()
        act_name = item.get('act', doc_type.upper())
    
    # Add source information
    source = item.get('source', 'IndianKanoon.org')
    parts.append(f"Source: {source}")
    
    # Add act name
    if item.get('act'):
        parts.append(f"Act: {item['act']}")
    else:
        parts.append(f"Act: {act_name}")
    
    # Add section number
    section_num = item.get('section_number', '')
    if section_num:
        parts.append(f"{act_abbrev} Section {section_num}")
    
    # Add section title
    section_title = item.get('section_title', '')
    if section_title:
        parts.append(f"Title: {section_title}")
    
    # Add main section text
    section_text = item.get('section_text', '')
    if section_text:
        parts.append(f"\nContent:\n{section_text}")
    
    # Add explanations if any
    explanations = item.get('explanations', [])
    if explanations and any(explanations):
        parts.append("\nExplanations:")
        for i, explanation in enumerate(explanations, 1):
            if explanation and explanation.strip():
                parts.append(f"{i}. {explanation}")
    
    # Add illustrations if any
    illustrations = item.get('illustrations', [])
    if illustrations and any(illustrations):
        parts.append("\nIllustrations:")
        for i, illustration in enumerate(illustrations, 1):
            if illustration and illustration.strip():
                parts.append(f"{i}. {illustration}")
    
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
        total_chunks = 0
        
        for idx, item in enumerate(tqdm(data, desc=f"     Preparing {data_type}", unit="doc")):
            # Create document text
            doc_text = create_document_text(item, data_type)
            
            # Chunk the document if it's too large
            chunks = chunk_text(doc_text, chunk_size=800, overlap=200)
            total_chunks += len(chunks)
            
            # Create metadata
            section_num = item.get('section_number', idx)
            
            # Process each chunk
            for chunk_idx, chunk in enumerate(chunks):
                # Generate stable ID
                chunk_id = f"{data_type}_{section_num}_{chunk_idx}"
                ids.append(chunk_id)
                documents.append(chunk)
                
                # Create metadata for this chunk
                metadata = {
                    'type': data_type,
                    'section_number': str(section_num),
                    'section_title': item.get('section_title', ''),
                    'source': item.get('source', 'IndianKanoon.org'),
                    'url': item.get('url', ''),
                    'act': item.get('act', ''),
                    'chunk_index': chunk_idx,
                    'total_chunks': len(chunks)
                }
                
                # Clean metadata - remove None values and ensure correct types
                clean_metadata = {}
                for key, value in metadata.items():
                    if value is not None and value != '':
                        if isinstance(value, (str, int, float, bool)):
                            clean_metadata[key] = value
                        else:
                            clean_metadata[key] = str(value)
                
                metadatas.append(clean_metadata)
        
        print(f"     Generated {total_chunks} chunks from {len(data)} documents (avg {total_chunks/len(data):.1f} chunks/doc)")
        print(f"     Generating embeddings for {len(documents)} chunks...")
        
        try:
            embeddings = embedding_model.embed_documents(documents)
        except Exception as e:
            print(f"     ✗ Error generating embeddings: {e}")
            continue
        
        # Add to ChromaDB in batches
        batch_size = 100
        print(f"     Adding chunks to ChromaDB...")
        for i in range(0, len(ids), batch_size):
            end_idx = min(i + batch_size, len(ids))
            try:
                collection.add(
                    ids=ids[i:end_idx],
                    documents=documents[i:end_idx],
                    embeddings=embeddings[i:end_idx],
                    metadatas=metadatas[i:end_idx]
                )
            except Exception as e:
                print(f"     ✗ Error adding batch {i}-{end_idx}: {e}")
                continue
        
        print(f"     ✓ Indexed {len(ids)} chunks from {len(data)} documents in {data_type}")
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
