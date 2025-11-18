# Quick Start Guide - Legal AI Assistant

## ⚡ Fast Setup (5 minutes)

### 1. Prerequisites Check
```powershell
# Check Python version (need 3.8+)
python --version

# Check if Ollama is installed
ollama --version
```

### 2. Install Ollama & Model
```powershell
# If Ollama not installed, download from https://ollama.ai
# Then pull Llama 3.3
ollama pull llama3.3

# Verify
ollama list
```

### 3. Install Python Dependencies
```powershell
# In project directory
cd E:\LawStreet

# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 4. Index Legal Data
```powershell
# This creates the vector database (takes 5-10 min first time)
python scripts/index_data.py
```

**Wait for:**
```
✓ Success! The vector database is ready.
```

### 5. Start Server
```powershell
# Start the API
python main.py
```

**Wait for:**
```
✓ RAG Pipeline initialized successfully
Uvicorn running on http://0.0.0.0:8000
```

### 6. Test It!

**Option A: Web Browser**
- Go to: http://localhost:8000/docs
- Click "POST /ask"
- Click "Try it out"
- Enter query: `{"query": "What is Section 302 IPC?"}`
- Click "Execute"

**Option B: PowerShell**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method POST -ContentType "application/json" -Body '{"query":"What is Section 302 IPC?"}'
```

**Option C: Python Script**
```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={"query": "What is the punishment for theft?"}
)

print(response.json()["answer"])
```

---

## 🎯 Sample Queries to Try

1. `"What is Section 302 IPC?"`
2. `"Explain Article 21 of the Constitution"`
3. `"What is the punishment for theft?"`
4. `"What does CrPC say about bail?"`
5. `"What are fundamental rights?"`

---

## 🐛 Troubleshooting

### "Could not connect to Ollama"
```powershell
# Start Ollama
ollama serve
```

### "Collection not found"
```powershell
# Re-run indexing
python scripts/index_data.py
```

### Import errors
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📚 Next Steps

- Read full documentation: `README.md`
- Review test cases: `ACCEPTANCE_TESTS.md`
- Customize prompt: Edit `model/prompt_template.txt`
- Add more data: Place JSON files in `Data/` and re-index

---

**You're all set! 🚀**
