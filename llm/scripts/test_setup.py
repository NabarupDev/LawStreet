"""
Test script to validate Legal AI setup and functionality
Run with: python scripts/test_setup.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all required packages are installed"""
    print("\n" + "="*60)
    print("Testing Python Package Imports")
    print("="*60)
    
    packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("chromadb", "ChromaDB"),
        ("sentence_transformers", "Sentence Transformers"),
        ("requests", "Requests"),
        ("pydantic", "Pydantic"),
        ("torch", "PyTorch"),
        ("tqdm", "tqdm")
    ]
    
    failed = []
    for package, name in packages:
        try:
            __import__(package)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT INSTALLED")
            failed.append(package)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    else:
        print("\n✓ All packages installed successfully")
        return True


def test_ollama():
    """Test Ollama connection"""
    print("\n" + "="*60)
    print("Testing Ollama Connection")
    print("="*60)
    
    import requests
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"  ✓ Ollama is running")
            print(f"  Available models: {len(models)}")
            
            # Check for llama3.3
            model_names = [m.get("name", "") for m in models]
            has_llama = any("llama3.3" in name.lower() for name in model_names)
            
            if has_llama:
                print("  ✓ Llama 3.3 model found")
                return True
            else:
                print("  ⚠ Llama 3.3 model NOT found")
                print("    Install with: ollama pull llama3.3")
                return False
        else:
            print(f"  ✗ Ollama responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("  ✗ Cannot connect to Ollama")
        print("    Ensure Ollama is running: ollama serve")
        print("    Or install from: https://ollama.ai")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_data_files():
    """Test that data files exist"""
    print("\n" + "="*60)
    print("Testing Data Files")
    print("="*60)
    
    from app.config import DATA_FILES
    
    found = 0
    missing = []
    
    for name, filepath in DATA_FILES.items():
        if filepath.exists():
            print(f"  ✓ {name}: {filepath.name}")
            found += 1
        else:
            print(f"  ✗ {name}: NOT FOUND at {filepath}")
            missing.append(name)
    
    if missing:
        print(f"\n⚠ Missing data files: {', '.join(missing)}")
        print("  Some functionality may be limited")
    else:
        print(f"\n✓ All {found} data files found")
    
    return found > 0


def test_chroma_collection():
    """Test ChromaDB collection"""
    print("\n" + "="*60)
    print("Testing ChromaDB Collection")
    print("="*60)
    
    try:
        import chromadb
        from chromadb.config import Settings
        from app.config import CHROMA_DIR, CHROMA_COLLECTION_NAME
        
        if not CHROMA_DIR.exists():
            print(f"  ✗ ChromaDB directory not found: {CHROMA_DIR}")
            print("    Run indexing script: python scripts/index_data.py")
            return False
        
        client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
            count = collection.count()
            
            print(f"  ✓ Collection found: {CHROMA_COLLECTION_NAME}")
            print(f"  ✓ Documents indexed: {count}")
            
            if count == 0:
                print("  ⚠ Collection is empty")
                print("    Run indexing script: python scripts/index_data.py")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ✗ Collection '{CHROMA_COLLECTION_NAME}' not found")
            print("    Run indexing script: python scripts/index_data.py")
            return False
            
    except Exception as e:
        print(f"  ✗ Error accessing ChromaDB: {e}")
        return False


def test_embedding_model():
    """Test embedding model loading"""
    print("\n" + "="*60)
    print("Testing Embedding Model")
    print("="*60)
    
    try:
        from app.embed import get_embedding_model
        
        print("  Loading model (may take a moment)...")
        model = get_embedding_model()
        
        print(f"  ✓ Model loaded: {model.model_name}")
        
        test_text = "Test legal document"
        embedding = model.embed_query(test_text)
        
        print(f"  ✓ Embedding generated (dimension: {len(embedding)})")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error loading embedding model: {e}")
        return False


def test_api_endpoint():
    """Test if API can be started (checks for port conflicts)"""
    print("\n" + "="*60)
    print("Testing API Configuration")
    print("="*60)
    
    try:
        import socket
        from app.config import API_PORT
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', API_PORT))
        
        if result == 0:
            print(f"  ⚠ Port {API_PORT} is already in use")
            print("    API may already be running, or another service is using the port")
            sock.close()
            return None 
        else:
            print(f"  ✓ Port {API_PORT} is available")
            sock.close()
            return True
            
    except Exception as e:
        print(f"  ⚠ Could not check port: {e}")
        return None


def run_quick_query_test():
    """Test a complete query flow"""
    print("\n" + "="*60)
    print("Testing Complete RAG Pipeline")
    print("="*60)
    
    try:
        from app.rag import get_rag_pipeline
        
        print("  Initializing RAG pipeline...")
        pipeline = get_rag_pipeline()
        
        print("  Executing test query...")
        test_query = "What is theft?"
        result = pipeline.ask(test_query)
        
        print(f"  ✓ Query executed successfully")
        print(f"  ✓ Retrieved {result['num_retrieved_docs']} documents")
        print(f"  ✓ Answer generated ({len(result['answer'])} characters)")
        
        if result['sources']:
            print(f"  ✓ Sources cited: {len(result['sources'])}")
        
        print(f"\n  Sample answer preview:")
        print(f"  {result['answer'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error in RAG pipeline: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Legal AI - System Validation Test")
    print("="*60)
    
    results = {
        "Package Imports": test_imports(),
        "Ollama Connection": test_ollama(),
        "Data Files": test_data_files(),
        "ChromaDB Collection": test_chroma_collection(),
        "Embedding Model": test_embedding_model(),
        "API Configuration": test_api_endpoint(),
    }
    
    if all([v for v in results.values() if v is not None]):
        results["RAG Pipeline"] = run_quick_query_test()
    else:
        print("\n⚠ Skipping pipeline test due to setup issues")
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result is True else ("✗ FAIL" if result is False else "⚠ SKIP")
        print(f"  {status}: {test_name}")
    
    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0 and passed > 0:
        print("\n🎉 All tests passed! System is ready.")
        print("   Start the server with: python main.py")
    else:
        print("\n⚠ Some tests failed. Please resolve issues above.")
        print("   See README.md for setup instructions.")
    
    print("="*60)


if __name__ == "__main__":
    main()
