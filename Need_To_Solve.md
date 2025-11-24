# 🧠 Indian Legal Assistant (LLM-Powered)

A lightweight AI-powered legal information assistant focused on **Indian Law**, designed to provide **accurate**, **context-aware**, and **safe** legal information to users.

This project solves a common problem:  
> Most LLMs provide **incorrect or irrelevant** legal answers when dealing with Indian law.

Examples of failures:
- Suggesting the RTI Act for private landlord disputes  
- Explaining the Indian Contract Act when it does not apply  
- Giving irrelevant textbook definitions instead of practical legal steps  
- Hallucinating fake Indian laws or sections  

To fix these issues, we use:
- A strongly engineered **legal system prompt**
- Strict **anti-hallucination rules**
- **Gemini** as the primary model  
- **OpenRouter models** as fallback options (free/cheaper alternatives)

---

## 🚩 Problem We Are Solving

Most open models fail for Indian legal queries due to:

### ❌ Hallucinations
Models often make up legal provisions, sections, or Acts.

### ❌ Wrong Act Mapping
Example:
- User asks about landlord refusing deposit → model responds with RTI Act  
- User asks about tenancy → model responds with Contract Act theory  

### ❌ No Legal Category Detection
Models do not classify the user query into:
- Landlord–tenant  
- Consumer dispute  
- Criminal offense  
- Cybercrime  
- Employment law  
- Contract dispute  
- Evidence law  

Correct legal reasoning depends on correct categorization.

---

## ✅ Our Solution

### ✔ 1. A strong, context-aware **System Prompt**
The assistant identifies the legal category and provides only **relevant Indian laws**, avoiding irrelevant Acts.

### ✔ 2. Hallucination Guardrails
The model is instructed:
- Not to invent laws  
- Not to create legal sections  
- Not to draft binding legal documents  
- To recommend consulting a lawyer when needed  

### ✔ 3. Model Routing System
We use:

### **Primary Model (Default)**
**Google Gemini 1.5 Pro**  
Best accuracy, lowest hallucination, best for legal reasoning.

### **Fallback / Backup Models (via OpenRouter)**
Used when:
- Free usage required  
- Gemini fails  
- Model needs variety

Possible fallback models:
- DeepSeek-R1-Distill-Qwen (great free reasoning model)  
- Llama 3.1 70B (if free quota available)  
- Qwen 2.5 14B  

These models work as backup when Gemini is unavailable or rate-limited.

---