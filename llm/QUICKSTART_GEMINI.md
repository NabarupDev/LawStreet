# 🚀 Quick Start Guide - Gemini Integration

## What Changed?

Your LawStreet application now uses **Google Gemini** instead of Ollama for generating responses. This means:

✅ No need to install or run Ollama locally  
✅ Faster response times with cloud-based inference  
✅ Access to Google's powerful AI models  
✅ Better scalability and reliability  

## Quick Setup (3 Steps)

### Step 1: Get Your Gemini API Key (FREE)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key (starts with `AIza...`)

### Step 2: Configure Your Environment

1. Open the `.env` file in the `llm/` folder
2. Replace `your_gemini_api_key_here` with your actual API key:

```env
GEMINI_API_KEY=AIzaSyC...your_actual_key_here
GEMINI_MODEL=gemini-1.5-flash
```

3. Save the file

### Step 3: Test & Run

```powershell
# Test Gemini connection
cd e:\LawStreet\llm
python test_gemini.py

# If test passes, start the server
python -m app.main
```

## Example Test Output

```
============================================================
Testing Gemini API Integration
============================================================

✓ API Key found: AIzaSyC...xyz
✓ Model: gemini-1.5-flash

------------------------------------------------------------
Testing simple query...
------------------------------------------------------------

✓ Gemini Response: Hello, Legal AI is working!

============================================================
✓ SUCCESS! Gemini API is working correctly
============================================================

You can now run the full RAG system with:
  python -m app.main
```

## Troubleshooting

### ❌ "API Key not configured"
**Solution**: Make sure you've edited the `.env` file and saved it with your actual API key.

### ❌ "Invalid API key"
**Solution**: Double-check your API key is correct. Get a new one from Google AI Studio if needed.

### ❌ "API quota exceeded"
**Solution**: 
- Free tier: 15 requests per minute
- Wait a minute and try again
- Or upgrade to paid tier for higher limits

### ❌ "Module 'google.generativeai' not found"
**Solution**: Install the package:
```powershell
pip install google-generativeai
```

## Available Models

| Model | Speed | Quality | Cost | Best For |
|-------|-------|---------|------|----------|
| `gemini-1.5-flash` | ⚡ Fast | ⭐⭐⭐ Good | 💰 Free tier | Production, quick queries |
| `gemini-1.5-pro` | 🐌 Slower | ⭐⭐⭐⭐⭐ Excellent | 💰💰 Pay per use | Complex legal analysis |

To change models, edit `GEMINI_MODEL` in your `.env` file.

## Testing the Full System

```powershell
# Start the server
python -m app.main

# In another terminal, test a query
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method POST -ContentType "application/json" -Body '{"query":"What is IPC Section 420?"}'
```

## Next Steps

1. ✅ Configure API key in `.env`
2. ✅ Run `python test_gemini.py` to verify
3. ✅ Start server with `python -m app.main`
4. ✅ Open browser to http://localhost:8000/docs
5. ✅ Try sample queries in the interactive API docs

## Support

- **Gemini API Docs**: https://ai.google.dev/docs
- **Get API Key**: https://makersuite.google.com/app/apikey
- **Pricing Info**: https://ai.google.dev/pricing

---

**Need Help?** Check `GEMINI_MIGRATION.md` for detailed technical information.
