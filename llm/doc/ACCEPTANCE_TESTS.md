# Acceptance Tests - Legal AI Assistant

This document provides comprehensive test cases to validate the RAG system's functionality.

## 🎯 Test Objectives

- Verify accurate retrieval of legal documents
- Validate answer quality and relevance
- Ensure proper source citation
- Test edge cases and error handling
- Confirm system performance

---

## ✅ Test Cases

### Test Category 1: Indian Penal Code (IPC) Queries

#### Test 1.1: Direct Section Query
**Query:** `"What is Section 302 IPC?"`

**Expected Answer Pattern:**
- Should mention "murder" or "causing death"
- Should reference "punishment of death or imprisonment for life"
- Should cite Section 302 explicitly
- Source should be "Indian Penal Code"

**Success Criteria:**
- ✅ Accurate description of murder under IPC 302
- ✅ Correct punishment details mentioned
- ✅ Section 302 cited in sources
- ✅ Response time < 10 seconds

---

#### Test 1.2: Offense-Based Query
**Query:** `"What is the punishment for theft in India?"`

**Expected Answer Pattern:**
- Should reference IPC Section 379
- Should mention "imprisonment up to 3 years" or "fine" or "both"
- Should define theft or reference dishonest taking of property
- May also reference Section 378 (definition of theft)

**Success Criteria:**
- ✅ Mentions IPC Section 379
- ✅ Includes punishment details
- ✅ Clear and understandable explanation
- ✅ Sources include IPC sections 378 and/or 379

---

#### Test 1.3: Multiple Related Sections
**Query:** `"What are the laws regarding dowry in IPC?"`

**Expected Answer Pattern:**
- Should reference Section 304B (dowry death) and/or Section 498A (cruelty)
- Should explain the offense and punishment
- May include definitions and scope

**Success Criteria:**
- ✅ At least one relevant IPC section cited
- ✅ Accurate description of dowry-related offenses
- ✅ Punishment details included
- ✅ Multiple sources if available

---

### Test Category 2: Constitution of India

#### Test 2.1: Fundamental Rights
**Query:** `"What does the Constitution say about the right to equality?"`

**Expected Answer Pattern:**
- Should reference Article 14 (Equality before law)
- May reference Articles 15, 16 (prohibition of discrimination)
- Should explain equality principle
- Source should be "Constitution of India"

**Success Criteria:**
- ✅ Article 14 mentioned
- ✅ Clear explanation of equality principle
- ✅ Constitution cited as source
- ✅ Contextually accurate

---

#### Test 2.2: Specific Article Query
**Query:** `"Explain Article 21 of Indian Constitution"`

**Expected Answer Pattern:**
- Should state "Protection of life and personal liberty"
- Should mention "No person shall be deprived of life or personal liberty except according to procedure established by law"
- Should cite Article 21 explicitly

**Success Criteria:**
- ✅ Accurate text or paraphrase of Article 21
- ✅ Article number explicitly mentioned
- ✅ Correct constitutional context
- ✅ Source shows Constitution

---

### Test Category 3: Criminal Procedure Code (CrPC)

#### Test 3.1: Procedural Query
**Query:** `"What does CrPC say about arrest procedures?"`

**Expected Answer Pattern:**
- Should reference relevant CrPC sections on arrest (e.g., Sections 41, 46, 50)
- Should mention arrest procedures, warrants, or rights of arrested persons
- Source should be "Code of Criminal Procedure"

**Success Criteria:**
- ✅ Mentions CrPC sections related to arrest
- ✅ Describes arrest procedures or rights
- ✅ Legally accurate information
- ✅ CrPC cited as source

---

#### Test 3.2: Bail Provisions
**Query:** `"What are the bail provisions in CrPC?"`

**Expected Answer Pattern:**
- Should reference Sections 436, 437, 438, 439 (bail provisions)
- Should explain types of offenses and bail eligibility
- Should mention anticipatory bail or regular bail

**Success Criteria:**
- ✅ Relevant CrPC sections cited
- ✅ Bail concepts explained
- ✅ Distinguishes between bailable/non-bailable if applicable
- ✅ Accurate legal terminology

---

### Test Category 4: Evidence Act

#### Test 4.1: Evidence Rules
**Query:** `"What does the Evidence Act say about confession?"`

**Expected Answer Pattern:**
- Should reference relevant sections on confession (e.g., Sections 24-30)
- Should explain admissibility of confession
- Source should be "Indian Evidence Act"

**Success Criteria:**
- ✅ Mentions Evidence Act sections
- ✅ Explains confession rules
- ✅ Accurate legal principles
- ✅ Evidence Act cited

---

### Test Category 5: Complex/Ambiguous Queries

#### Test 5.1: Broad Topic Query
**Query:** `"What are the laws on cybercrime?"`

**Expected Answer Pattern:**
- Should retrieve relevant IPC sections (e.g., 66, 66A if IT Act data present)
- OR should honestly state limited information if no specific cyber laws in database
- Should not fabricate laws

**Success Criteria:**
- ✅ Either provides relevant sections OR states limitation
- ✅ Does not hallucinate non-existent laws
- ✅ Maintains accuracy
- ✅ Transparent about information availability

---

#### Test 5.2: Out-of-Scope Query
**Query:** `"What is the capital of France?"`

**Expected Answer Pattern:**
- Should state this is outside the scope of Indian legal information
- Should NOT attempt to answer non-legal questions
- May redirect to legal queries

**Success Criteria:**
- ✅ Does not provide answer to non-legal question
- ✅ Politely indicates out of scope
- ✅ Maintains focus on legal domain
- ✅ No retrieved documents or low relevance scores

---

### Test Category 6: Source Citation & Accuracy

#### Test 6.1: Source Verification
**Query:** `"What is Section 498A IPC?"`

**Expected Answer Pattern:**
- Clear answer about cruelty by husband or relatives
- Section 498A explicitly mentioned
- IPC cited in sources list

**Success Criteria:**
- ✅ Answer matches legal definition
- ✅ Sources array contains IPC reference
- ✅ Section number appears in sources
- ✅ Distance/relevance score reasonable (< 0.5)

---

### Test Category 7: Edge Cases

#### Test 7.1: Very Short Query
**Query:** `"Murder"`

**Expected Answer Pattern:**
- Should retrieve IPC Section 302
- Should provide definition and punishment
- Should handle single-word query gracefully

**Success Criteria:**
- ✅ Returns relevant answer
- ✅ IPC Section 302 in results
- ✅ Does not error out
- ✅ Contextual response

---

#### Test 7.2: Very Long Query
**Query:** `"I want to know about all the provisions related to theft, robbery, dacoity, and other property crimes including punishments, procedures, and any related sections in IPC, CrPC, and Evidence Act"`

**Expected Answer Pattern:**
- Should handle long query without errors
- Should retrieve multiple relevant sections
- Should synthesize coherent answer
- May prioritize most relevant aspects

**Success Criteria:**
- ✅ No timeout or error
- ✅ Retrieves 5+ documents
- ✅ Provides structured answer
- ✅ Covers multiple aspects of query

---

#### Test 7.3: Empty or Invalid Query
**Query:** `""`

**Expected Behavior:**
- Should return validation error
- Should not crash server
- Should provide helpful error message

**Success Criteria:**
- ✅ HTTP 422 Unprocessable Entity OR appropriate error
- ✅ Error message mentions query required
- ✅ Server remains operational

---

## 🔍 Performance Tests

### Performance Test 1: Response Time
**Query:** `"What is Section 420 IPC?"`

**Expected Performance:**
- First query (cold start): < 10 seconds
- Subsequent queries: < 5 seconds
- Average response time: 2-4 seconds

**Success Criteria:**
- ✅ Cold start < 10s
- ✅ Warm queries < 5s
- ✅ No memory leaks over 100 queries

---

### Performance Test 2: Concurrent Requests
**Test:** Send 5 concurrent queries

**Expected Behavior:**
- All requests complete successfully
- No crashes or timeouts
- Reasonable response times (< 15s each)

**Success Criteria:**
- ✅ All 5 requests return 200 OK
- ✅ All answers are relevant
- ✅ No server errors

---

## 🧪 Integration Tests

### Integration Test 1: End-to-End Flow
**Steps:**
1. Send POST request to `/ask`
2. Verify embedding generated
3. Verify ChromaDB query executed
4. Verify Ollama called
5. Verify response structure

**Success Criteria:**
- ✅ All pipeline steps execute
- ✅ Response includes answer, query, sources, num_retrieved_docs
- ✅ Sources array has 1-5 items
- ✅ Answer is non-empty string

---

### Integration Test 2: Health Check
**Query:** `GET /health`

**Expected Response:**
```json
{
  "status": "healthy",
  "collection": "indian_law_collection",
  "document_count": <number>,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

**Success Criteria:**
- ✅ Returns 200 OK
- ✅ document_count > 0
- ✅ Status is "healthy"

---

## 📋 Manual Testing Checklist

### Pre-Testing Checklist
- [ ] Ollama is running (`ollama list` shows llama3.3)
- [ ] ChromaDB indexed (`vectorstore/chroma/` exists with data)
- [ ] API server started (port 8000 accessible)
- [ ] Virtual environment activated
- [ ] All dependencies installed

### During Testing
- [ ] Test at least 3 IPC queries
- [ ] Test at least 2 Constitution queries
- [ ] Test at least 1 CrPC query
- [ ] Test 1 edge case (empty/invalid query)
- [ ] Test 1 out-of-scope query
- [ ] Verify source citations in all responses
- [ ] Check response times are reasonable
- [ ] Visit `/docs` and test via Swagger UI

### Post-Testing
- [ ] No server crashes during tests
- [ ] Log file shows no critical errors
- [ ] Memory usage stable
- [ ] All test results documented

---

## 🎯 Expected Answer Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Accuracy** | >90% | Answers match legal provisions |
| **Relevance** | >85% | Retrieved docs relevant to query |
| **Citation** | 100% | All answers cite sources |
| **Completeness** | >80% | Answers address full question |
| **Response Time** | <5s avg | Time from request to response |
| **Error Rate** | <5% | Failed/error responses |

---

## 🐛 Known Limitations to Verify

1. **Limited to indexed documents** - Cannot answer about laws not in database
2. **No real-time updates** - Static data; doesn't reflect latest amendments
3. **Context window limits** - Very long legal texts may be truncated
4. **Model hallucination** - LLM may occasionally generate plausible but incorrect info
5. **No legal advice** - Provides information only, not professional advice

**Testing Tip:** Verify system handles these limitations gracefully with honest responses.

---

## 📊 Test Results Template

```
Test Date: [DATE]
Tester: [NAME]
System Version: [VERSION]

Test Results:
✅ PASS | ❌ FAIL | ⚠️ PARTIAL

Category 1: IPC Queries
- Test 1.1: ✅ PASS
- Test 1.2: ✅ PASS
- Test 1.3: ✅ PASS

Category 2: Constitution
- Test 2.1: ✅ PASS
- Test 2.2: ✅ PASS

[... continue for all categories ...]

Overall Score: X/Y tests passed
Pass Rate: XX%

Issues Found:
1. [Description]
2. [Description]

Recommendations:
1. [Recommendation]
2. [Recommendation]
```

---

**Happy Testing! 🚀**
