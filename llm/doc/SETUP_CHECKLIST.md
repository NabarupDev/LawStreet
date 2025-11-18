# Setup Checklist - Legal AI Assistant

## ✅ What You Need to Do Before Running the System

### 1. Install Ollama
- Download and install Ollama from: https://ollama.ai
- Ollama is the local LLM runtime that will run Llama 3.3

### 2. Pull Llama 3.3 Model
```powershell
ollama pull llama3.3
```
This downloads the Llama 3.3 model (~2GB). First time only.

### 3. Verify Ollama is Running
```powershell
# Check Ollama service is running
ollama list

# Should show llama3.3 in the list
```

### 4. Install Python Dependencies
```powershell
# In the project directory
cd E:\LawStreet

# Optional: Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install all required packages
pip install -r requirements.txt
```

**What gets installed:**
- FastAPI (web framework)
- ChromaDB (vector database)
- sentence-transformers (embedding model ~80MB download)
- PyTorch (required for transformers)
- Other supporting libraries

### 5. Index Your Legal Data
```powershell
# This converts JSON files to embeddings and stores in ChromaDB
# Takes 5-10 minutes first time
python scripts\index_data.py
```

**What happens:**
- Loads all JSON files from Data/ folder
- Chunks long documents (800 chars with 200 char overlap)
- Generates embeddings using sentence-transformers
- Stores in vectorstore/chroma/ directory
- You'll see progress bars for each file

### 6. Validate Setup (Optional but Recommended)
```powershell
# Run validation script to check everything
python scripts\test_setup.py
```

**This checks:**
- All Python packages installed
- Ollama is running and has llama3.3
- Data files exist
- ChromaDB collection created and populated
- Embedding model works
- Can run a test query

### 7. Start the API Server
```powershell
# Start the server
python main.py
```

**Server starts at:** http://localhost:8000

**You should see:**
```
✓ RAG Pipeline initialized successfully
Uvicorn running on http://0.0.0.0:8000
```

### 8. Test the System
**Option A - Browser:**
- Go to: http://localhost:8000/docs
- Try the POST /ask endpoint
- Enter: `{"query": "What is Section 302 IPC?"}`

**Option B - PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method POST -ContentType "application/json" -Body '{"query":"What is Section 302 IPC?"}'
```

---

## 📋 Summary Checklist

Before first run:
- [ ] Ollama installed
- [ ] `ollama pull llama3.3` completed
- [ ] `ollama list` shows llama3.3
- [ ] `pip install -r requirements.txt` completed
- [ ] `python scripts\index_data.py` completed successfully
- [ ] `python scripts\test_setup.py` shows all tests passed (optional)

To run system:
- [ ] Ollama is running (check with `ollama list`)
- [ ] Run `python main.py`
- [ ] Test at http://localhost:8000/docs

---

## 🔧 What's Already Done

✅ All project files created  
✅ Configuration set up  
✅ Data files present in Data/ folder  
✅ Scripts ready to run  
✅ Documentation complete  

---

## ⏱️ Time Estimates

- Ollama installation: 2-3 minutes
- Llama 3.3 download: 3-5 minutes (~2GB)
- Python dependencies: 5-10 minutes (includes sentence-transformers model download)
- Data indexing: 5-10 minutes (first time)
- **Total first-time setup: 15-30 minutes**

After first setup, starting the system takes only seconds!

---

## ❓ Common Issues

**"ollama: command not found"**
- Ollama not installed or not in PATH
- Install from https://ollama.ai and restart terminal

**"Could not connect to Ollama"**
- Ollama service not running
- Start it: `ollama serve` or ensure it's running in background

**"Collection not found"**
- Haven't run indexing script yet
- Run: `python scripts\index_data.py`

**Import errors during pip install**
- Try: `pip install -r requirements.txt --force-reinstall`
- Or install packages individually

**Indexing takes too long**
- Normal for first time (downloading embedding model)
- Should be faster on subsequent runs

---

## 🎯 Quick Start Command Sequence

```powershell
# 1. Install Ollama (manual - from website)
# 2. Pull model
ollama pull llama3.3

# 3. Install Python deps
pip install -r requirements.txt

# 4. Index data
python scripts\index_data.py

# 5. Validate (optional)
python scripts\test_setup.py

# 6. Start server
python main.py

# 7. Test in browser
# Visit: http://localhost:8000/docs
```

---

**You're ready to go once all checkboxes above are complete! 🚀**
