"""
Test Ollama API integration
Run this after starting Ollama: ollama serve
And pulling the model: ollama pull phi4-mini
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
import requests

print("=" * 60)
print("Testing Ollama API Integration")
print("=" * 60)

print(f"\n✓ Ollama URL: {OLLAMA_BASE_URL}")
print(f"✓ Model: {OLLAMA_MODEL}")

# Check if Ollama is running
try:
    response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
    if response.status_code != 200:
        print(f"\n❌ ERROR: Ollama returned status {response.status_code}")
        sys.exit(1)
    
    # Check if model is available
    models = response.json().get("models", [])
    model_names = [m.get("name", "").split(":")[0] for m in models]
    
    if OLLAMA_MODEL not in model_names and f"{OLLAMA_MODEL}:latest" not in [m.get("name", "") for m in models]:
        print(f"\n⚠ Model '{OLLAMA_MODEL}' not found in Ollama.")
        print(f"Available models: {model_names}")
        print(f"\nPlease pull the model with: ollama pull {OLLAMA_MODEL}")
        sys.exit(1)
    
    print(f"\n✓ Ollama is running and model '{OLLAMA_MODEL}' is available")

except requests.exceptions.ConnectionError:
    print(f"\n❌ ERROR: Cannot connect to Ollama at {OLLAMA_BASE_URL}")
    print("\nPlease follow these steps:")
    print("1. Install Ollama from: https://ollama.ai")
    print("2. Start Ollama with: ollama serve")
    print(f"3. Pull the model with: ollama pull {OLLAMA_MODEL}")
    print("4. Run this test again")
    sys.exit(1)

# Test the API
try:
    print("\n" + "-" * 60)
    print("Testing simple query...")
    print("-" * 60)
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": "Say 'Hello, Legal AI is working!' in one short sentence.",
        "stream": False,
        "options": {
            "num_predict": 50
        }
    }
    
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        answer = result.get("response", "")
        if answer:
            print(f"\n✓ Ollama Response: {answer}")
            print("\n" + "=" * 60)
            print("✓ SUCCESS! Ollama API is working correctly")
            print("=" * 60)
            print("\nYou can now run the full RAG system with:")
            print("  python -m app.main")
        else:
            print("\n❌ ERROR: No response from Ollama")
    else:
        print(f"\n❌ ERROR: Ollama returned status {response.status_code}")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nCommon issues:")
    print("- Ollama not running (start with: ollama serve)")
    print(f"- Model not pulled (run: ollama pull {OLLAMA_MODEL})")
    print("- Insufficient memory for model")
