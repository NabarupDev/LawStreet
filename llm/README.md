# Legal AI - Indian Law Assistant (RAG System)

A complete Retrieval-Augmented Generation (RAG) system for querying Indian legal documents using **Ollama/Gemini + ChromaDB + Sentence Transformers**.

## 🎯 Project Overview

This project provides a FastAPI-based backend that allows users to ask questions about Indian law and receive accurate answers based on legal documents including:

- **Indian Penal Code (IPC)**
- **Code of Criminal Procedure (CrPC)**
- **Code of Civil Procedure (CPC)**
- **Indian Evidence Act**

### Key Features

✅ **FastAPI Backend** - RESTful API with POST `/ask` endpoint  
✅ **RAG Pipeline** - Retrieval + Prompt Building + LLM Generation  
✅ **ChromaDB Vector Store** - Persistent embeddings storage  
✅ **Sentence Transformers** - MiniLM-L6-v2 for embeddings  
✅ **Flexible LLM Support** - Choose between Ollama (local) or Gemini (cloud)  
✅ **Ollama Support** - Run phi4-mini locally with no rate limits  
✅ **Google Gemini API** - Powerful cloud-based LLM alternative  
✅ **Structured Data** - Pre-processed JSON legal documents from IndianKanoon.org  
✅ **Source Citations** - Answers include relevant section references

## 🔀 Switching Between LLM Providers

You can easily switch between **Ollama (local)** and **Gemini (cloud)** by changing one environment variable:

### Using Ollama (Local, No Rate Limits)
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi4-mini
```

**Setup:**
1. Install Ollama: https://ollama.ai
2. Run: `ollama serve`
3. Pull model: `ollama pull phi4-mini`

### Using Gemini (Cloud, Faster)
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

**Setup:**
1. Get API key from: https://makersuite.google.com/app/apikey
2. Install: `pip install google-generativeai`

### Comparison

| Feature | Ollama (phi4-mini) | Gemini (1.5-flash) |
|---------|-------------------|-------------------|
| Cost | Free | Free tier available |
| Rate Limits | None | Yes (15 RPM) |
| Privacy | Complete (local) | Cloud-based |
| Speed | ~135s per query | ~3-5s per query |
| Setup | Requires local GPU/CPU | API key only |
| Reasoning | Excellent | Excellent |  

---

## 📁 Project Structure

```
LawStreet/
│
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration settings
│   ├── embed.py             # Embedding model (sentence-transformers)
│   ├── main.py              # FastAPI application
│   ├── rag.py               # RAG pipeline logic
│   └── utils.py             # Utility functions
│
├── Data/
│   ├── ipc.json             # Indian Penal Code sections
│   ├── crpc.json            # Criminal Procedure Code
│   ├── constitution.json    # Constitution of India
│   ├── evidence.json        # Indian Evidence Act
│   ├── acts.json            # Other acts (HMA, MVA, etc.)
│   └── raw/                 # Raw source data (optional)
│
├── model/
│   └── prompt_template.txt  # Llama 3.3 prompt template
│
├── scripts/
│   ├── index_data.py        # Index JSON data to ChromaDB
│   └── clean_data.py        # Data cleaning utilities
│
├── vectorstore/
│   └── chroma/              # ChromaDB persistent storage (created after indexing)
│
├── main.py                  # Alternative entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## 🚀 Setup Instructions

### Prerequisites

1. **Python 3.8+** installed
2. **Google Gemini API Key** ([Get API Key](https://makersuite.google.com/app/apikey))

### Step 1: Configure Gemini API

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Copy `.env.example` to `.env`:
   ```powershell
   cp .env.example .env
   ```
3. Edit `.env` and replace `your_gemini_api_key_here` with your actual API key:
   ```
   GEMINI_API_KEY=AIza...your_actual_key_here
   GEMINI_MODEL=gemini-1.5-flash
   ```

### Step 2: Clone/Setup Project

```powershell
# Navigate to project directory
cd E:\LawStreet
```

### Step 3: Install Python Dependencies

```powershell
# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**Dependencies installed:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `chromadb` - Vector database
- `sentence-transformers` - Embedding model
- `torch` - PyTorch (for transformers)
- `google-generativeai` - Gemini API client
- `python-dotenv` - Environment variable loading
- `tqdm` - Progress bars
- `pydantic` - Data validation

### Step 4: Index Legal Data

This step converts JSON legal documents into embeddings and stores them in ChromaDB.

```powershell
# Run the indexing script
python scripts/index_data.py
```

**Expected output:**
```
============================================================
Legal AI - Data Indexing Script
============================================================

1. Initializing ChromaDB at: E:\LawStreet\vectorstore\chroma
   Created collection: indian_law_collection

2. Loading embedding model...
   Model loaded: sentence-transformers/all-MiniLM-L6-v2

3. Loading and indexing legal documents...

   Processing ipc...
     Loaded XXX documents
     Generating embeddings for XXX documents...
     ✓ Indexed XXX documents from ipc

   [... more files processed ...]

============================================================
Indexing Complete!
Total documents indexed: XXXX
Collection: indian_law_collection
Location: E:\LawStreet\vectorstore\chroma
============================================================

✓ Success! The vector database is ready.
  You can now run the API server with: python -m app.main
```

**Note:** First-time indexing will download the sentence-transformers model (~80MB) and may take 5-10 minutes depending on data size.

### Step 5: Test Gemini Integration (Optional)

Before starting the full server, test that Gemini is working:

```powershell
python test_gemini.py
```

### Step 6: Start the API Server

```powershell
# Run the FastAPI server
python -m app.main
```

**Or alternatively:**
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Expected output:**
```
RAG Pipeline initialized with Gemini model: gemini-1.5-flash
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 📡 API Usage

### Endpoint: `POST /ask`

**Request:**
```json
{
  "query": "What is the punishment for theft under IPC?"
}
```

**Response:**
```json
{
  "answer": "Under Section 379 of the Indian Penal Code, theft (defined as dishonestly taking movable property...) is punishable with imprisonment of either description for a term which may extend to three years, or with fine, or with both.",
  "query": "What is the punishment for theft under IPC?",
  "num_retrieved_docs": 5,
  "sources": [
    {
      "source": "Indian Penal Code",
      "section": "379",
      "distance": 0.234
    },
    {
      "source": "Indian Penal Code",
      "section": "378",
      "distance": 0.267
    }
  ]
}
```

### Testing with curl

```powershell
# Windows PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method POST -ContentType "application/json" -Body '{"query":"What is Section 302 IPC?"}'
```

### Testing with Python

```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={"query": "What is the punishment for murder?"}
)

print(response.json()["answer"])
```

### Interactive API Documentation

Visit **http://localhost:8000/docs** for Swagger UI with interactive API testing.

### Health Check

```powershell
# Check API health
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

---

## 🧪 Testing & Validation

### Quick Test Questions

Try these sample questions to validate the system:

1. **"What is Section 302 IPC?"** - Should return information about murder
2. **"Explain the right to equality under the Constitution"** - Should reference Article 14
3. **"What is the punishment for theft?"** - Should cite IPC Section 379
4. **"What does CrPC say about arrest procedures?"** - Should return CrPC sections
5. **"What is dowry prohibition?"** - Should reference relevant act

### Expected Behavior

✅ **Accurate answers** based on retrieved legal documents  
✅ **Source citations** with section/article numbers  
✅ **Contextual responses** using 3-5 relevant documents  
✅ **Honest limitations** - states when context is insufficient  
✅ **Fast responses** - typically 2-5 seconds per query  

### Running Acceptance Tests

See `ACCEPTANCE_TESTS.md` for detailed test cases and expected answer patterns.

---

## 🔧 Configuration

Edit `app/config.py` to customize:

```python
# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Number of documents to retrieve
TOP_K_RESULTS = 5

# Ollama settings
OLLAMA_MODEL = "llama3.3"
OLLAMA_BASE_URL = "http://localhost:11434"

# Context window
MAX_CONTEXT_LENGTH = 4000
```

---

## 🐛 Troubleshooting

### Issue: "Could not connect to Ollama"

**Solution:**
```powershell
# Ensure Ollama is running
ollama list

# Start Ollama service if needed
ollama serve
```

### Issue: "Collection not found"

**Solution:**
```powershell
# Re-run the indexing script
python scripts/index_data.py
```

### Issue: "No documents retrieved"

**Possible causes:**
1. ChromaDB collection is empty - reindex data
2. Query embedding failed - check embedding model
3. Data files missing - verify `Data/` folder contents

**Solution:**
```powershell
# Check collection status
python -c "import chromadb; client = chromadb.PersistentClient(path='vectorstore/chroma'); print(client.get_collection('indian_law_collection').count())"
```

### Issue: Slow response times

**Solutions:**
1. Reduce `TOP_K_RESULTS` in config (fewer documents = faster)
2. Use smaller Ollama model (e.g., `llama3.2:1b`)
3. Reduce `MAX_CONTEXT_LENGTH`

### Issue: Out of memory during indexing

**Solution:**
```powershell
# Index files one at a time by modifying scripts/index_data.py
# Or increase system RAM/swap space
```

### Issue: Import errors

**Solution:**
```powershell
# Ensure you're in the project root and virtual environment is activated
cd E:\LawStreet
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **Index Time** | ~5-10 min (first time) |
| **Embedding Model Size** | ~80 MB |
| **Query Latency** | 2-5 seconds |
| **Documents Indexed** | ~2000-5000 (varies by data) |
| **Embedding Dimension** | 384 |
| **RAM Usage** | ~2-4 GB |

---

## 🔒 Limitations & Disclaimers

⚠️ **This is NOT legal advice** - This system provides legal information only  
⚠️ **Verify critical information** - Always consult official legal sources  
⚠️ **Model limitations** - LLM may occasionally generate incorrect information  
⚠️ **Data currency** - Legal documents may not reflect latest amendments  
⚠️ **Local deployment** - All processing happens locally (privacy-friendly)  

---

## 🛠️ Advanced Usage

### Custom Prompt Templates

Edit `model/prompt_template.txt` to customize how Llama 3.3 responds:

```plaintext
You are a legal assistant...

Context:
{context}

Question: {question}

Answer: [Your custom instructions]
```

### Adding New Legal Documents

1. Add JSON file to `Data/` folder with schema:
```json
[
  {
    "id": "unique_id",
    "type": "act_type",
    "section": "123",
    "section_title": "Title",
    "content": "Legal text...",
    "metadata": {
      "source": "Act Name",
      "section": "123"
    }
  }
]
```

2. Update `app/config.py`:
```python
DATA_FILES = {
    "new_act": DATA_DIR / "new_act.json"
}
```

3. Re-index:
```powershell
python scripts/index_data.py
```

### Using Different Ollama Models

```powershell
# Pull alternative model
ollama pull llama3.2

# Update config.py
OLLAMA_MODEL = "llama3.2"

# Restart server
```

---

## 📚 Additional Resources

- **Ollama Documentation:** https://ollama.ai
- **ChromaDB Documentation:** https://docs.trychroma.com
- **FastAPI Documentation:** https://fastapi.tiangolo.com
- **Sentence Transformers:** https://www.sbert.net

---

## 📝 License

This project is for educational and informational purposes only.

---

## 👥 Support

For issues or questions:
1. Check **Troubleshooting** section above
2. Verify all setup steps completed
3. Check Ollama service status
4. Review API logs for error messages

---

**Built with ❤️ for legal AI education**
