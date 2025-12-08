"""
Web Search Module using Tavily API

PURPOSE:
Provides fallback web search functionality when local ChromaDB doesn't have
relevant information for a legal query. Uses Tavily API for accurate legal search.

USAGE:
When RAG retrieval returns low-relevance results (high distance scores),
use this module to search the web for authoritative legal information.
"""
import os
from typing import List, Dict, Any, Optional
import httpx

from app.config import (
    TAVILY_API_KEY,
    TAVILY_SEARCH_DEPTH,
    TAVILY_MAX_RESULTS
)


class TavilySearchError(Exception):
    """Custom exception for Tavily search errors"""
    pass


def search_legal_web(query: str, max_results: int = TAVILY_MAX_RESULTS) -> Dict[str, Any]:
    """
    Search the web for legal information using Tavily API.
    
    Args:
        query: The legal query to search for
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary with search results:
        {
            "success": bool,
            "results": [
                {
                    "title": str,
                    "url": str,
                    "content": str,
                    "score": float
                }
            ],
            "answer": str (if available),
            "error": str (if failed)
        }
    """
    if not TAVILY_API_KEY:
        return {
            "success": False,
            "results": [],
            "error": "Tavily API key not configured. Please set TAVILY_API_KEY in .env file."
        }
    
    try:
        # Enhance query for Indian legal context
        enhanced_query = f"Indian law legal {query}"
        
        # Tavily API request
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": enhanced_query,
                "search_depth": TAVILY_SEARCH_DEPTH,
                "max_results": max_results,
                "include_answer": True,
                "include_domains": [
                    "indiankanoon.org",
                    "legislative.gov.in",
                    "indiacode.nic.in",
                    "lawmin.gov.in",
                    "sci.gov.in",
                    "lawrato.com",
                    "livelaw.in",
                    "barandbench.com"
                ]
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "results": [],
                "error": f"Tavily API error: {response.status_code} - {response.text}"
            }
        
        data = response.json()
        
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score", 0.0)
            })
        
        return {
            "success": True,
            "results": results,
            "answer": data.get("answer", ""),
            "query": query
        }
        
    except httpx.TimeoutException:
        return {
            "success": False,
            "results": [],
            "error": "Web search timed out. Please try again."
        }
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "error": f"Web search failed: {str(e)}"
        }


def format_web_results_as_context(search_results: Dict[str, Any], max_content_length: int = 800) -> str:
    """
    Format web search results into a context string for the LLM.
    Keeps content concise to reduce response time.
    
    Args:
        search_results: Results from search_legal_web()
        max_content_length: Maximum characters per result content
        
    Returns:
        Formatted context string
    """
    if not search_results.get("success") or not search_results.get("results"):
        return "General legal principles apply. Specifics may vary by situation."
    
    context_parts = []
    context_parts.append("**Legal Information from Authoritative Sources:**\n")
    
    for idx, result in enumerate(search_results["results"][:2], 1):  # Limit to 2 for speed
        content = result.get('content', '')
        # Truncate long content
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        doc_text = f"\n[Source {idx}: {result.get('title', 'Legal Resource')}]\n"
        doc_text += f"{content}\n"
        context_parts.append(doc_text)
    
    return "\n".join(context_parts)
    
    return "\n".join(context_parts)


def is_tavily_configured() -> bool:
    """Check if Tavily API is properly configured"""
    return bool(TAVILY_API_KEY)
