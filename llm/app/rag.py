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
        5. Configure Gemini API with API key from environment
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
    
    def query_gemini(prompt: str) -> str:
        // STEP 6: Call Gemini API with generation config
        Uses Google Generative AI SDK
        
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
        - "Error: Invalid or missing Gemini API key. Please check your .env file"
        - "Error: Request timed out. Query may be too complex."
        - "Error: Gemini API quota exceeded. Please check your usage limits"
        
        EDGE CASES:
        - Empty response from model -> "No answer generated"
        - Malformed JSON -> Log and return error
        - Model returns refusal -> Pass through to user
    
    def ask(query: str) -> dict:
        // MAIN ORCHESTRATION METHOD
        1. retrieved_docs = retrieve_documents(query, top_k=5)
        2. context = build_context(retrieved_docs)
        3. prompt = build_prompt(query, context)
        4. answer = query_gemini(prompt)
        
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
        - If Gemini API fails: Return with answer=<error_message>, sources=[]
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
- Set appropriate timeouts for Gemini API
- Monitor API quota usage
- Log timing for each step (debug mode)

SINGLETON PATTERN:
Global _rag_pipeline variable ensures only ONE instance created across all requests.
This avoids reloading models and reconnecting to ChromaDB on every query.
"""
import chromadb
from chromadb.config import Settings
import requests
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re
import json

from app.config import (
    CHROMA_DIR,
    CHROMA_COLLECTION_NAME,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_TIMEOUT,
    TOP_K_RESULTS,
    PROMPT_TEMPLATE_PATH,
    MAX_CONTEXT_LENGTH,
    RELEVANCE_THRESHOLD,
    USE_GEMINI_FOR_WEB_SEARCH,
    LLM_MIDDLEWARE_PROVIDER
)
from app.embed import get_embedding_model
from app.web_search import search_legal_web, format_web_results_as_context, is_tavily_configured
from app.response_processor import post_process_response

# Import LLM Middleware client
llm_middleware_client = None
if LLM_PROVIDER == "middleware":
    try:
        from app.llm_middleware import get_llm_client
        llm_middleware_client = get_llm_client
    except ImportError as e:
        print(f"Warning: Could not import LLM middleware client: {e}")
        print("Make sure websocket-client is installed: pip install websocket-client")

genai = None
if LLM_PROVIDER == "gemini" or USE_GEMINI_FOR_WEB_SEARCH:
    try:
        import google.generativeai as genai
    except ImportError:
        print("Warning: google-generativeai not installed. Install with: pip install google-generativeai")
        if LLM_PROVIDER == "gemini":
            print("ERROR: Gemini selected but library not installed!")
        genai = None


def extract_section_info(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract section number and act type from a query.
    
    Handles patterns like:
    - "IPC 420", "ipc section 420", "section 420 ipc"
    - "CrPC 41", "crpc section 41"
    - "Section 302", "sec 302"
    
    Returns:
        Tuple of (section_number, act_type) or (None, None) if not found
    """
    query_lower = query.lower()
    
    patterns = [
        r'\b(ipc|crpc|cpc|evidence)\s*(?:section)?\s*(\d+)\b',
        r'\bsection\s*(\d+)\s*(?:of\s*)?(ipc|crpc|cpc|evidence)?\b',
        r'\bsec\.?\s*(\d+)\b',
        r'\bwhat\s+is\s+(\d+)\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            groups = match.groups()
            
            if pattern == patterns[0]:
                act_type = groups[0]
                section_num = groups[1]
            elif pattern == patterns[1]: 
                section_num = groups[0]
                act_type = groups[1] if len(groups) > 1 and groups[1] else None
            else: 
                section_num = groups[0]
                act_type = None
            
            if act_type is None:
                act_type = 'ipc'
                
            return section_num, act_type
    
    return None, None


def expand_query_for_section(query: str, section_num: str, act_type: str) -> str:
    """
    Expand a query about a specific section to improve semantic matching.
    
    Adds relevant keywords based on the act type.
    """
    act_names = {
        'ipc': 'Indian Penal Code IPC offense crime punishment penalty',
        'crpc': 'Code of Criminal Procedure CrPC criminal procedure bail arrest',
        'cpc': 'Code of Civil Procedure CPC civil procedure suit decree',
        'evidence': 'Indian Evidence Act evidence witness proof testimony'
    }
    
    act_keywords = act_names.get(act_type, '')
    
    expanded = f"Section {section_num} {act_type.upper()} {act_keywords} {query}"
    return expanded


class RAGPipeline:
    """Retrieval-Augmented Generation Pipeline"""
    
    def __init__(self):
        """Initialize the RAG pipeline"""
        self.llm_provider = LLM_PROVIDER
        self.use_gemini_for_web = USE_GEMINI_FOR_WEB_SEARCH
        
        if self.llm_provider == "middleware":
            # Use Open LLM Middleware for multi-provider support
            if llm_middleware_client is None:
                raise ImportError("LLM Middleware client not available. Check the import errors above.")
            
            self.middleware_client = llm_middleware_client()
            print(f"RAG Pipeline initialized with Open LLM Middleware (provider: {LLM_MIDDLEWARE_PROVIDER})")
            
        elif self.llm_provider == "ollama":
            self.ollama_base_url = OLLAMA_BASE_URL
            self.ollama_model = OLLAMA_MODEL
            
            try:
                response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                if response.status_code != 200:
                    print(f"Warning: Ollama may not be running at {self.ollama_base_url}")
            except requests.exceptions.ConnectionError:
                print(f"Warning: Cannot connect to Ollama at {self.ollama_base_url}. Make sure Ollama is running.")
            
            print(f"RAG Pipeline initialized with Ollama model: {OLLAMA_MODEL}")
            
        elif self.llm_provider == "gemini":
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not found. Please set it in .env file.")
            if genai is None:
                raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
            
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel(GEMINI_MODEL)
            print(f"RAG Pipeline initialized with Gemini model: {GEMINI_MODEL}")
        else:
            raise ValueError(f"Invalid LLM_PROVIDER: {self.llm_provider}. Use 'ollama', 'gemini', or 'middleware'")
        
        if self.use_gemini_for_web and self.llm_provider == "ollama":
            if GEMINI_API_KEY and genai is not None:
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel(GEMINI_MODEL)
                print(f"Gemini ({GEMINI_MODEL}) enabled for web search results (faster)")
            else:
                print("Warning: USE_GEMINI_FOR_WEB_SEARCH=true but Gemini not configured. Will use Ollama for all queries.")
                self.use_gemini_for_web = False
        
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.chroma_client.get_collection(
            name=CHROMA_COLLECTION_NAME
        )
        
        self.embedding_model = get_embedding_model()
        
        self.prompt_template = self._load_prompt_template()
    
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
        Retrieve relevant documents from ChromaDB using hybrid search.
        
        When a specific section number is detected in the query (e.g., "IPC 420"),
        the method first tries to fetch that exact section, then supplements with
        semantic search results.
        
        Args:
            query: User query string
            top_k: Number of documents to retrieve
            
        Returns:
            List of retrieved documents with metadata
        """
        retrieved_docs = []
        section_num, act_type = extract_section_info(query)
        
        if section_num and act_type:
            try:
                exact_results = self.collection.get(
                    where={
                        "$and": [
                            {"section_number": section_num},
                            {"type": act_type}
                        ]
                    },
                    include=["documents", "metadatas"]
                )
                
                if exact_results['ids']:
                    for idx, doc_id in enumerate(exact_results['ids']):
                        retrieved_docs.append({
                            "content": exact_results['documents'][idx],
                            "metadata": exact_results['metadatas'][idx] if exact_results['metadatas'] else {},
                            "distance": 0.0  
                        })
                    print(f"Found exact match for {act_type.upper()} Section {section_num}")
            except Exception as e:
                print(f"Error in exact match search: {e}")
        
        search_query = query
        if section_num and act_type:
            search_query = expand_query_for_section(query, section_num, act_type)
        
        query_embedding = self.embedding_model.embed_query(search_query)
        
        remaining_results = top_k - len(retrieved_docs)
        if remaining_results > 0:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=remaining_results + len(retrieved_docs),  # Get extra to filter duplicates
                include=["documents", "metadatas", "distances"]
            )
            
            if results['documents'] and len(results['documents'][0]) > 0:
                existing_ids = set()
                for doc in retrieved_docs:
                    meta = doc.get('metadata', {})
                    existing_ids.add(f"{meta.get('type', '')}_{meta.get('section_number', '')}")
                
                for idx, doc in enumerate(results['documents'][0]):
                    if len(retrieved_docs) >= top_k:
                        break
                    
                    meta = results['metadatas'][0][idx] if results['metadatas'] else {}
                    doc_id = f"{meta.get('type', '')}_{meta.get('section_number', '')}"
                    
                    if doc_id in existing_ids:
                        continue
                    
                    retrieved_docs.append({
                        "content": doc,
                        "metadata": meta,
                        "distance": results['distances'][0][idx] if results['distances'] else 0
                    })
                    existing_ids.add(doc_id)
        
        return retrieved_docs
    
    def build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved documents
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant legal documents were found for this query."
        
        context_parts = []
        current_length = 0
        
        for idx, doc in enumerate(documents, 1):
            metadata = doc.get('metadata', {})
            content = doc.get('content', '')
            
            doc_text = f"\n--- Document {idx} ---\n"
            
            doc_type = metadata.get('type', '')
            section_num = metadata.get('section_number', metadata.get('section', ''))
            section_title = metadata.get('section_title', '')
            
            if doc_type == 'ipc':
                doc_text += f"Indian Penal Code (IPC) - Section {section_num}\n"
            elif doc_type == 'crpc':
                doc_text += f"Code of Criminal Procedure (CrPC) - Section {section_num}\n"
            elif doc_type == 'cpc':
                doc_text += f"Code of Civil Procedure (CPC) - Section {section_num}\n"
            elif doc_type == 'evidence':
                doc_text += f"Indian Evidence Act - Section {section_num}\n"
            else:
                if 'source' in metadata:
                    doc_text += f"Source: {metadata['source']}\n"
                if section_num:
                    doc_text += f"Section: {section_num}\n"
            
            if section_title:
                clean_title = section_title.replace('in The', ' - ').replace('in TheIndian', ' - ')
                doc_text += f"Title: {clean_title}\n"
            
            doc_text += f"\n{content}\n"
            doc_text += "---\n"
            
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
    
    def query_llm(self, prompt: str) -> str:
        """
        Send prompt to the configured LLM and get response
        
        Args:
            prompt: Complete prompt string
            
        Returns:
            Model response text
        """
        if self.llm_provider == "middleware":
            return self._query_middleware(prompt)
        elif self.llm_provider == "ollama":
            return self._query_ollama(prompt)
        elif self.llm_provider == "gemini":
            return self._query_gemini(prompt)
        else:
            return f"Error: Unknown LLM provider: {self.llm_provider}"
    
    def _query_middleware(self, prompt: str) -> str:
        """
        Send prompt to Open LLM Middleware and get response
        
        Args:
            prompt: Complete prompt string
            
        Returns:
            Model response text
        """
        import time
        
        try:
            print(f"Sending request to LLM Middleware...")
            print(f"Prompt length: {len(prompt)} characters")
            start_time = time.time()
            
            # Use the generate convenience method
            response = self.middleware_client.generate(
                prompt=prompt,
                system_prompt="You are a knowledgeable legal assistant specializing in Indian law."
            )
            
            elapsed = time.time() - start_time
            print(f"Middleware response received in {elapsed:.2f} seconds")
            
            return response
            
        except Exception as e:
            return f"Error querying LLM Middleware: {str(e)}"
    
    def _query_ollama(self, prompt: str) -> str:
        """
        Send prompt to Ollama and get response
        
        Args:
            prompt: Complete prompt string
            
        Returns:
            Model response text
        """
        import time
        
        try:
            print(f"Sending request to Ollama ({self.ollama_model})...")
            print(f"Prompt length: {len(prompt)} characters")
            start_time = time.time()
            
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 512,  # Reduced for faster response
                    "num_ctx": 4096,     # Context window
                    "num_gpu": 1         # Use GPU if available
                }
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=OLLAMA_TIMEOUT
            )
            
            elapsed = time.time() - start_time
            print(f"Ollama response received in {elapsed:.2f} seconds")
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response generated from Ollama")
            else:
                return f"Error: Ollama returned status code {response.status_code}"
            
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Make sure Ollama is running with 'ollama serve'"
        except requests.exceptions.Timeout:
            return "Error: Request timed out. The model may be loading or the query is too complex."
        except Exception as e:
            return f"Error querying Ollama: {str(e)}"
    
    def _query_gemini(self, prompt: str) -> str:
        """
        Send prompt to Gemini and get response
        
        Args:
            prompt: Complete prompt string
            
        Returns:
            Model response text
        """
        import time
        
        try:
            print(f"Sending request to Gemini ({GEMINI_MODEL})...")
            print(f"Prompt length: {len(prompt)} characters")
            start_time = time.time()
            
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                max_output_tokens=2048,
            )
            
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options={'timeout': GEMINI_TIMEOUT}
            )
            
            elapsed = time.time() - start_time
            print(f"Gemini response received in {elapsed:.2f} seconds")
            
            if response and response.text:
                return response.text
            else:
                return "No response generated from Gemini"
            
        except Exception as e:
            error_msg = str(e)
            if "API_KEY" in error_msg.upper():
                return "Error: Check your Gemini API key in the .env file."
            elif "quota" in error_msg.lower():
                return "Error: Gemini API quota exceeded. Please check your usage limits."
            elif "timeout" in error_msg.lower():
                return "Error: Request timed out. Please try again."
            else:
                return f"Error querying Gemini: {error_msg}"
    
    def _check_relevance(self, retrieved_docs: List[Dict[str, Any]], query: str) -> bool:
        """
        Check if retrieved documents are relevant enough.
        
        Returns True if documents are relevant (should use local DB),
        Returns False if we should fall back to web search.
        """
        if not retrieved_docs:
            return False
        
        best_distance = retrieved_docs[0].get('distance', 1.0)
        if best_distance == 0.0:
            return True
        
        section_num, act_type = extract_section_info(query)
        
        if section_num and act_type:
            for doc in retrieved_docs:
                meta = doc.get('metadata', {})
                if (meta.get('section_number') == section_num and 
                    meta.get('type') == act_type):
                    return True
            return False
        
        return best_distance < RELEVANCE_THRESHOLD
    
    def ask(self, query: str) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve, build prompt, and generate answer.
        Falls back to web search if local data is not relevant.
        
        Args:
            query: User question
            
        Returns:
            Dictionary with answer and metadata
        """
        retrieved_docs = self.retrieve_documents(query)
        
        use_local_db = self._check_relevance(retrieved_docs, query)
        used_web_search = False
        web_search_results = None
        
        if use_local_db:
            context = self.build_context(retrieved_docs)
        else:
            print(f"Local DB not relevant enough, trying web search for: {query}")
            
            if is_tavily_configured():
                web_search_results = search_legal_web(query)
                
                if web_search_results.get("success") and web_search_results.get("results"):
                    used_web_search = True
                    context = format_web_results_as_context(web_search_results)
                    print(f"Web search returned {len(web_search_results['results'])} results")
                else:
                    context = self.build_context(retrieved_docs)
                    if not retrieved_docs:
                        context = f"No relevant information found in local database or web search for: {query}"
            else:
                context = self.build_context(retrieved_docs)
                print("Tavily not configured, using local DB results")
        
        prompt = self.build_prompt(query, context)
        
        if used_web_search and self.use_gemini_for_web and hasattr(self, 'gemini_model'):
            print("Using Gemini for web search results (faster)")
            raw_answer = self._query_gemini(prompt)
        elif self.llm_provider == "middleware":
            raw_answer = self._query_middleware(prompt)
        elif self.llm_provider == "ollama":
            raw_answer = self._query_ollama(prompt)
        else:
            raw_answer = self._query_gemini(prompt)
        
        answer = post_process_response(raw_answer, query)
        
        sources = []
        
        if used_web_search and web_search_results:
            for result in web_search_results.get("results", [])[:3]:
                sources.append({
                    "source": result.get("title", "Web Source"),
                    "section": "Web",
                    "type": "web",
                    "url": result.get("url", ""),
                    "distance": round(1.0 - result.get("score", 0), 3)
                })
        else:
            for doc in retrieved_docs[:3]:
                meta = doc.get('metadata', {})
                doc_type = meta.get('type', '')
                section_num = meta.get('section_number', meta.get('section', meta.get('article', 'N/A')))
                
                if doc_type == 'ipc':
                    source_name = f"IPC Section {section_num}"
                elif doc_type == 'crpc':
                    source_name = f"CrPC Section {section_num}"
                elif doc_type == 'cpc':
                    source_name = f"CPC Section {section_num}"
                elif doc_type == 'evidence':
                    source_name = f"Evidence Act Section {section_num}"
                else:
                    source_name = meta.get('source', 'Unknown')
                
                sources.append({
                    "source": source_name,
                    "section": str(section_num),
                    "type": doc_type,
                    "url": meta.get('url', ''),
                    "distance": round(doc.get('distance', 0), 3)
                })
        
        return {
            "answer": answer,
            "query": query,
            "num_retrieved_docs": len(retrieved_docs),
            "used_web_search": used_web_search,
            "sources": sources
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