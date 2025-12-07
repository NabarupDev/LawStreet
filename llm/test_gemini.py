"""
Test Gemini API integration
Run this after setting your GEMINI_API_KEY in .env file
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import GEMINI_API_KEY, GEMINI_MODEL
import google.generativeai as genai

print("=" * 60)
print("Testing Gemini API Integration")
print("=" * 60)

# Check if API key is configured
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print("\n❌ ERROR: GEMINI_API_KEY not configured!")
    print("\nPlease follow these steps:")
    print("1. Get your API key from: https://makersuite.google.com/app/apikey")
    print("2. Open the .env file in llm/ directory")
    print("3. Replace 'your_gemini_api_key_here' with your actual API key")
    print("4. Save the file and run this test again")
    sys.exit(1)

print(f"\n✓ API Key found: {GEMINI_API_KEY[:10]}...{GEMINI_API_KEY[-4:]}")
print(f"✓ Model: {GEMINI_MODEL}")

# Test the API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    print("\n" + "-" * 60)
    print("Testing simple query...")
    print("-" * 60)
    
    response = model.generate_content("Say 'Hello, Legal AI is working!'")
    
    if response and response.text:
        print(f"\n✓ Gemini Response: {response.text}")
        print("\n" + "=" * 60)
        print("✓ SUCCESS! Gemini API is working correctly")
        print("=" * 60)
        print("\nYou can now run the full RAG system with:")
        print("  python -m app.main")
    else:
        print("\n❌ ERROR: No response from Gemini")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nCommon issues:")
    print("- Invalid API key")
    print("- API quota exceeded")
    print("- Network connectivity issues")
    print("- Incorrect model name")
