"""
RAG Pipeline: Retrieval-Augmented Generation for Legal Queries

PURPOSE:
Orchestrates the complete RAG workflow from query to answer, combining document retrieval,
context building, prompt engineering, and LLM generation.

PSEUDO-CODE WORKFLOW:

class RAGPipeline:
    def __init__():
        // Initialize ONCE on server startup
        1. Connect to ChromaDB persistent client at vectorstore/chroma/
        2. Get existing collection 'indian_law_collection' (error if not exists)
        3. Load embedding model singleton (sentence-transformers/all-MiniLM-L6-v2)
        4. Load prompt template from model/prompt_template.txt
        5. Verify Ollama is accessible (optional health check)
        6. Log successful initialization
    
    def retrieve_documents(query: str, top_k: int = 5):
        // STEP 1: Embed the query
        1. Call embedding_model.embed_query(query) -> vector[384]
        2. Handle embedding errors (return empty if fails)
        
        // STEP 2: Query ChromaDB
        3. collection.query(
             query_embeddings=[vector],
             n_results=top_k,
             include=["documents", "metadatas", "distances"]
           )
        4. Returns: {
             'documents': [[doc1_text, doc2_text, ...]],
             'metadatas': [[{source, section, chunk_index, title, ...}, ...]],
             'distances': [[0.234, 0.267, ...]]  // cosine distance
           }
        
        // STEP 3: Format retrieved results
        5. For each retrieved document, extract:
           - content: full chunk text
           - metadata.source: "Indian Penal Code", "Constitution of India", etc.
           - metadata.section: "420", "Article 21", etc.
           - metadata.title: section title/heading
           - metadata.chunk_index: which chunk of the section (if chunked)
           - metadata.act: act abbreviation (IPC, CrPC, etc.)
           - distance: similarity score (0.0 = identical, higher = less similar)
        
        6. Return list of dicts: [{content, metadata, distance}, ...]
        7. If no documents found (empty result), return empty list
    
    def build_context(documents: list[dict]) -> str:
        // STEP 4: Build context string from retrieved documents
        1. Initialize context_parts = []
        2. Track current_length to enforce MAX_CONTEXT_LENGTH (4000 chars)
        
        3. For each document (in order of relevance):
           Format as:
           ---
           [Document {index}]
           Source: {metadata.source}
           Section: {metadata.section}
           Title: {metadata.title}
           Chunk: {metadata.chunk_index} (if applicable)
           
           Content:
           {document.content}
           ---
           
        4. Accumulate formatted documents until MAX_CONTEXT_LENGTH reached
        5. Join all document strings with newlines
        6. Return formatted_context string
        
        EDGE CASE: If first document exceeds MAX_CONTEXT_LENGTH, truncate it
        EDGE CASE: If no documents, return "No relevant legal documents found."
    
    def build_prompt(query: str, context: str) -> str:
        // STEP 5: Fill prompt template
        1. Load template from self.prompt_template (cached from init)
        2. Replace {context} placeholder with formatted context string
        3. Replace {question} placeholder with user query
        4. Return complete prompt ready for LLM
        
        Template structure:
        - System instructions (legal assistant role, accuracy requirements)
        - Context section (retrieved legal documents)
        - Question section (user's query)
        - Answer section (instructions for response format)
    
    def query_ollama(prompt: str) -> str:
        // STEP 6: Call Ollama with retry logic
        URL: http://localhost:11434/api/generate
        
        REQUEST PAYLOAD:
        {
          "model": "llama3.3",
          "prompt": <complete_prompt_string>,
          "stream": false,  // Get complete response at once
          "options": {
            "temperature": 0.7,  // Balanced creativity/accuracy
            "top_p": 0.9,        // Nucleus sampling
            "top_k": 40,         // Token selection diversity
            "num_predict": 1024  // Max tokens to generate
          }
        }
        
        RETRY LOGIC:
        1. Attempt 1: Call with timeout=90s
        2. If ConnectionError: Wait 2s, retry (max 2 retries)
        3. If Timeout: Return error message to user (don't retry, too slow)
        4. If HTTP 4xx/5xx: Log error, return error message
        5. If success: Parse JSON response
        
        RESPONSE PARSING:
        {
          "model": "llama3.3",
          "created_at": "...",
          "response": "<generated_answer_text>",  // EXTRACT THIS
          "done": true
        }
        
        Extract response["response"] field as answer text
        
        ERROR RETURNS:
        - "Error: Could not connect to Ollama. Ensure it's running."
        - "Error: Request timed out. Query may be too complex."
        - "Error: Ollama returned error: {details}"
        
        EDGE CASES:
        - Empty response from model -> "No answer generated"
        - Malformed JSON -> Log and return error
        - Model returns refusal -> Pass through to user
    
    def ask(query: str) -> dict:
        // MAIN ORCHESTRATION METHOD
        1. retrieved_docs = retrieve_documents(query, top_k=5)
        2. context = build_context(retrieved_docs)
        3. prompt = build_prompt(query, context)
        4. answer = query_ollama(prompt)
        
        5. Return structured response:
        {
          "answer": answer,                    // Generated text from Llama
          "query": query,                      // Echo original query
          "num_retrieved_docs": len(retrieved_docs),
          "sources": [
            {
              "source": doc.metadata.source,
              "section": doc.metadata.section OR doc.metadata.article,
              "distance": round(doc.distance, 3)
            }
            for doc in retrieved_docs[:3]  // Top 3 most relevant
          ]
        }
        
        ERROR HANDLING:
        - If retrieve fails: Return with answer="Error during retrieval"
        - If Ollama fails: Return with answer=<error_message>, sources=[]
        - If any exception: Log full traceback, return generic error

METADATA FIELDS EXPECTED FROM CHROMADB:
- source: "Indian Penal Code", "Constitution of India", "Code of Criminal Procedure", etc.
- section: "420", "302", "46", etc. (string, not int)
- article: "21", "14", etc. (for Constitution)
- title: Human-readable section title
- chunk_index: 0, 1, 2... if document was split into chunks
- act: "IPC", "CrPC", "Constitution", "Evidence Act"
- type: "ipc", "constitution", "crpc", etc.
- original_id: Source document ID before chunking

PERFORMANCE CONSIDERATIONS:
- Cache embedding model (singleton)
- Reuse ChromaDB client connection
- Set appropriate timeouts
- Use connection pooling for Ollama (future)
- Log timing for each step (debug mode)

SINGLETON PATTERN:
Global _rag_pipeline variable ensures only ONE instance created across all requests.
This avoids reloading models and reconnecting to ChromaDB on every query.
"""
import chromadb
from chromadb.config import Settings
import requests
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.config import (
    CHROMA_DIR,
    CHROMA_COLLECTION_NAME,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    TOP_K_RESULTS,
    PROMPT_TEMPLATE_PATH,
    MAX_CONTEXT_LENGTH
)
from app.embed import get_embedding_model


class RAGPipeline:
    """Retrieval-Augmented Generation Pipeline"""
    
    def __init__(self):
        """Initialize the RAG pipeline"""
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.chroma_client.get_collection(
            name=CHROMA_COLLECTION_NAME
        )
        
        self.embedding_model = get_embedding_model()
        
        self.prompt_template = self._load_prompt_template()
        
        print(f"RAG Pipeline initialized with collection: {CHROMA_COLLECTION_NAME}")
    
    def _load_prompt_template(self) -> str:
        """Load the prompt template from file"""
        try:
            with open(PROMPT_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return """You are a knowledgeable legal assistant specializing in Indian law. Use the provided legal context to answer the user's question accurately and concisely.

Context:
{context}

Question: {question}

Answer: Provide a clear, accurate answer based on the legal context above. Cite specific sections, articles, or legal provisions when relevant. If the context doesn't contain enough information to answer the question, say so honestly."""
    
    def retrieve_documents(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from ChromaDB
        
        Args:
            query: User query string
            top_k: Number of documents to retrieve
            
        Returns:
            List of retrieved documents with metadata
        """
        query_embedding = self.embedding_model.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        retrieved_docs = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for idx, doc in enumerate(results['documents'][0]):
                retrieved_docs.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][idx] if results['metadatas'] else {},
                    "distance": results['distances'][0][idx] if results['distances'] else 0
                })
        
        return retrieved_docs
    
    def build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved documents
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0
        
        for idx, doc in enumerate(documents, 1):
            metadata = doc.get('metadata', {})
            content = doc.get('content', '')
            
            doc_text = f"\n[Document {idx}]\n"
            
            if 'source' in metadata:
                doc_text += f"Source: {metadata['source']}\n"
            if 'section' in metadata:
                doc_text += f"Section: {metadata['section']}\n"
            if 'article' in metadata:
                doc_text += f"Article: {metadata['article']}\n"
            if 'chapter_title' in metadata:
                doc_text += f"Chapter: {metadata['chapter_title']}\n"
            
            doc_text += f"Content: {content}\n"
            
            if current_length + len(doc_text) > MAX_CONTEXT_LENGTH:
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        return "\n".join(context_parts)
    
    def build_prompt(self, query: str, context: str) -> str:
        """
        Build the final prompt using template
        
        Args:
            query: User query
            context: Retrieved context
            
        Returns:
            Formatted prompt string
        """
        prompt = self.prompt_template.format(
            context=context,
            question=query
        )
        return prompt
    
    def query_ollama(self, prompt: str) -> str:
        """
        Send prompt to Ollama and get response
        
        Args:
            prompt: Complete prompt string
            
        Returns:
            Model response text
        """
        url = f"{OLLAMA_BASE_URL}/api/generate"
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=OLLAMA_TIMEOUT
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', 'No response generated')
            
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to Ollama. Please ensure Ollama is running on http://localhost:11434"
        except requests.exceptions.Timeout:
            return "Error: Request to Ollama timed out. The query may be too complex."
        except Exception as e:
            return f"Error querying Ollama: {str(e)}"
    
    def ask(self, query: str) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve, build prompt, and generate answer
        
        Args:
            query: User question
            
        Returns:
            Dictionary with answer and metadata
        """
        retrieved_docs = self.retrieve_documents(query)
        
        context = self.build_context(retrieved_docs)
        
        prompt = self.build_prompt(query, context)
        
        answer = self.query_ollama(prompt)
        
        return {
            "answer": answer,
            "query": query,
            "num_retrieved_docs": len(retrieved_docs),
            "sources": [
                {
                    "source": doc.get('metadata', {}).get('source', 'Unknown'),
                    "section": str(doc.get('metadata', {}).get('section', doc.get('metadata', {}).get('article', 'N/A'))),
                    "distance": round(doc.get('distance', 0), 3)
                }
                for doc in retrieved_docs[:3]  # Top 3 sources
            ]
        }


_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """
    Get or create the global RAG pipeline instance
    
    Returns:
        RAGPipeline instance
    """
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
