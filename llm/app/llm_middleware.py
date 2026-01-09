"""
Open LLM Middleware Client for Legal AI RAG System

PURPOSE:
Provides a client to interact with the Open LLM Middleware server, supporting
multiple providers (OpenAI, Google Gemini, Cerebras, Groq) with automatic failover,
retry logic, and WebSocket support.

FEATURES:
- Multi-provider support via middleware
- Automatic failover with backup API keys
- Smart retry logic with exponential backoff
- Both REST API and WebSocket communication
- Rate limit tracking per provider
"""
import os
import json
import time
import asyncio
import threading
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum

import requests
import websocket

from app.config import (
    LLM_MIDDLEWARE_URL,
    LLM_MIDDLEWARE_SECRET,
    LLM_MIDDLEWARE_PROVIDER,
    LLM_MIDDLEWARE_MODEL,
    LLM_MIDDLEWARE_TIMEOUT,
    LLM_MIDDLEWARE_MAX_TOKENS,
    LLM_MIDDLEWARE_USE_WEBSOCKET
)


class LLMProvider(Enum):
    """Supported LLM providers through the middleware"""
    OPENAI = "openai"
    GOOGLE = "google"
    CEREBRAS = "cerebras"
    GROQ = "groq"


@dataclass
class LLMResponse:
    """Structured response from LLM middleware"""
    content: str
    provider: str
    model: str
    attempts: int
    success: bool
    error: Optional[str] = None


class LLMMiddlewareClient:
    """
    Client for Open LLM Middleware server.
    
    Supports both REST API and WebSocket communication modes.
    Handles authentication, retry logic, and provider switching.
    """
    
    def __init__(
        self,
        base_url: str = None,
        secret_code: str = None,
        default_provider: str = None,
        default_model: str = None,
        timeout: int = None,
        max_tokens: int = None,
        use_websocket: bool = None
    ):
        """
        Initialize the LLM Middleware client.
        
        Args:
            base_url: Middleware server URL (e.g., https://open-llm-mslh.onrender.com)
            secret_code: Authentication secret code
            default_provider: Default LLM provider (openai, google, cerebras, groq)
            default_model: Default model to use (provider-specific)
            timeout: Request timeout in seconds
            max_tokens: Maximum tokens for response
            use_websocket: Whether to use WebSocket instead of REST API
        """
        self.base_url = (base_url or LLM_MIDDLEWARE_URL).rstrip('/')
        self.secret_code = secret_code or LLM_MIDDLEWARE_SECRET
        self.default_provider = default_provider or LLM_MIDDLEWARE_PROVIDER
        self.default_model = default_model or LLM_MIDDLEWARE_MODEL
        self.timeout = timeout or LLM_MIDDLEWARE_TIMEOUT
        self.max_tokens = max_tokens or LLM_MIDDLEWARE_MAX_TOKENS
        self.use_websocket = use_websocket if use_websocket is not None else LLM_MIDDLEWARE_USE_WEBSOCKET
        
        # WebSocket state
        self._ws: Optional[websocket.WebSocket] = None
        self._ws_authenticated = False
        self._ws_lock = threading.Lock()
        self._request_id_counter = 0
        
        # Validate configuration
        if not self.base_url:
            raise ValueError("LLM_MIDDLEWARE_URL not configured. Please set it in .env file.")
        if not self.secret_code:
            raise ValueError("LLM_MIDDLEWARE_SECRET not configured. Please set it in .env file.")
        
        print(f"LLM Middleware Client initialized:")
        print(f"  URL: {self.base_url}")
        print(f"  Provider: {self.default_provider}")
        print(f"  Model: {self.default_model or 'provider default'}")
        print(f"  Mode: {'WebSocket' if self.use_websocket else 'REST API'}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for REST API requests"""
        return {
            "Content-Type": "application/json",
            "x-secret-code": self.secret_code
        }
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID for WebSocket messages"""
        self._request_id_counter += 1
        return f"req_{int(time.time())}_{self._request_id_counter}"
    
    # ==================== REST API Methods ====================
    
    def chat_rest(
        self,
        messages: List[Dict[str, str]],
        provider: str = None,
        model: str = None,
        max_tokens: int = None
    ) -> LLMResponse:
        """
        Send a chat completion request via REST API.
        
        Args:
            messages: Array of message objects with 'role' and 'content'
            provider: LLM provider (defaults to configured provider)
            model: Model name (defaults to configured model)
            max_tokens: Max tokens in response (defaults to configured value)
            
        Returns:
            LLMResponse with content and metadata
        """
        provider = provider or self.default_provider
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens
        
        payload = {
            "provider": provider,
            "messages": messages,
            "maxTokens": max_tokens
        }
        
        # Only include model if explicitly set
        if model:
            payload["model"] = model
        
        try:
            print(f"Sending REST request to {self.base_url}/api/chat")
            print(f"  Provider: {provider}, Model: {model or 'default'}")
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            
            elapsed = time.time() - start_time
            print(f"Response received in {elapsed:.2f}s (status: {response.status_code})")
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract content from response
                content = ""
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if "message" in choice:
                        content = choice["message"].get("content", "")
                    elif "text" in choice:
                        content = choice["text"]
                
                # Extract metadata
                meta = data.get("_meta", {})
                
                return LLMResponse(
                    content=content,
                    provider=meta.get("provider", provider),
                    model=meta.get("model", model or "unknown"),
                    attempts=meta.get("attempts", 1),
                    success=True
                )
            
            elif response.status_code == 401:
                return LLMResponse(
                    content="",
                    provider=provider,
                    model=model or "unknown",
                    attempts=1,
                    success=False,
                    error="Authentication failed. Check your LLM_MIDDLEWARE_SECRET."
                )
            
            elif response.status_code == 429:
                return LLMResponse(
                    content="",
                    provider=provider,
                    model=model or "unknown",
                    attempts=1,
                    success=False,
                    error="Rate limit exceeded. The middleware will retry automatically."
                )
            
            else:
                error_text = response.text[:200] if response.text else "Unknown error"
                return LLMResponse(
                    content="",
                    provider=provider,
                    model=model or "unknown",
                    attempts=1,
                    success=False,
                    error=f"HTTP {response.status_code}: {error_text}"
                )
                
        except requests.exceptions.Timeout:
            return LLMResponse(
                content="",
                provider=provider,
                model=model or "unknown",
                attempts=1,
                success=False,
                error=f"Request timed out after {self.timeout}s. Try increasing LLM_MIDDLEWARE_TIMEOUT."
            )
        except requests.exceptions.ConnectionError:
            return LLMResponse(
                content="",
                provider=provider,
                model=model or "unknown",
                attempts=1,
                success=False,
                error=f"Cannot connect to middleware at {self.base_url}. Is the server running?"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                provider=provider,
                model=model or "unknown",
                attempts=1,
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    # ==================== WebSocket Methods ====================
    
    def _connect_websocket(self) -> bool:
        """
        Establish WebSocket connection and authenticate.
        
        Returns:
            True if connected and authenticated, False otherwise
        """
        with self._ws_lock:
            if self._ws and self._ws_authenticated:
                return True
            
            try:
                # Convert HTTP URL to WebSocket URL
                ws_url = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
                ws_url = f"{ws_url}/ws"
                
                print(f"Connecting to WebSocket: {ws_url}")
                
                self._ws = websocket.create_connection(
                    ws_url,
                    timeout=self.timeout
                )
                
                # Receive connection confirmation
                conn_msg = json.loads(self._ws.recv())
                if conn_msg.get("type") != "connected":
                    print(f"Unexpected connection message: {conn_msg}")
                
                # Authenticate
                auth_msg = {
                    "type": "auth",
                    "secretCode": self.secret_code
                }
                self._ws.send(json.dumps(auth_msg))
                
                # Wait for auth response
                auth_response = json.loads(self._ws.recv())
                
                if auth_response.get("type") == "auth_success":
                    self._ws_authenticated = True
                    print("WebSocket authenticated successfully")
                    return True
                else:
                    error = auth_response.get("message", "Authentication failed")
                    print(f"WebSocket authentication failed: {error}")
                    self._close_websocket()
                    return False
                    
            except Exception as e:
                print(f"WebSocket connection error: {e}")
                self._close_websocket()
                return False
    
    def _close_websocket(self):
        """Close WebSocket connection"""
        with self._ws_lock:
            if self._ws:
                try:
                    self._ws.close()
                except:
                    pass
                self._ws = None
            self._ws_authenticated = False
    
    def chat_websocket(
        self,
        messages: List[Dict[str, str]],
        provider: str = None,
        model: str = None,
        max_tokens: int = None
    ) -> LLMResponse:
        """
        Send a chat completion request via WebSocket.
        
        Args:
            messages: Array of message objects with 'role' and 'content'
            provider: LLM provider (defaults to configured provider)
            model: Model name (defaults to configured model)
            max_tokens: Max tokens in response (defaults to configured value)
            
        Returns:
            LLMResponse with content and metadata
        """
        provider = provider or self.default_provider
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens
        
        # Ensure WebSocket is connected
        if not self._connect_websocket():
            # Fall back to REST API
            print("WebSocket connection failed, falling back to REST API")
            return self.chat_rest(messages, provider, model, max_tokens)
        
        try:
            request_id = self._generate_request_id()
            
            request = {
                "type": "chat",
                "requestId": request_id,
                "provider": provider,
                "messages": messages,
                "maxTokens": max_tokens
            }
            
            if model:
                request["model"] = model
            
            print(f"Sending WebSocket chat request (ID: {request_id})")
            start_time = time.time()
            
            self._ws.send(json.dumps(request))
            
            # Wait for response
            while True:
                response_raw = self._ws.recv()
                response = json.loads(response_raw)
                
                # Match by request ID or accept if no request ID in response
                if response.get("requestId") == request_id or response.get("type") in ["chat_response", "chat_error"]:
                    break
            
            elapsed = time.time() - start_time
            print(f"WebSocket response received in {elapsed:.2f}s")
            
            if response.get("type") == "chat_response":
                # Extract content from response
                content = ""
                choices = response.get("choices", [])
                if choices:
                    choice = choices[0]
                    if "message" in choice:
                        content = choice["message"].get("content", "")
                    elif "text" in choice:
                        content = choice["text"]
                
                meta = response.get("_meta", {})
                
                return LLMResponse(
                    content=content,
                    provider=meta.get("provider", provider),
                    model=meta.get("model", model or "unknown"),
                    attempts=meta.get("attempts", 1),
                    success=True
                )
            
            elif response.get("type") == "chat_error":
                return LLMResponse(
                    content="",
                    provider=provider,
                    model=model or "unknown",
                    attempts=1,
                    success=False,
                    error=response.get("message", "Unknown error from middleware")
                )
            
            else:
                return LLMResponse(
                    content="",
                    provider=provider,
                    model=model or "unknown",
                    attempts=1,
                    success=False,
                    error=f"Unexpected response type: {response.get('type')}"
                )
                
        except websocket.WebSocketTimeoutException:
            self._close_websocket()
            return LLMResponse(
                content="",
                provider=provider,
                model=model or "unknown",
                attempts=1,
                success=False,
                error=f"WebSocket request timed out after {self.timeout}s"
            )
        except Exception as e:
            self._close_websocket()
            return LLMResponse(
                content="",
                provider=provider,
                model=model or "unknown",
                attempts=1,
                success=False,
                error=f"WebSocket error: {str(e)}"
            )
    
    # ==================== Main Chat Method ====================
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        provider: str = None,
        model: str = None,
        max_tokens: int = None
    ) -> LLMResponse:
        """
        Send a chat completion request using configured transport (REST or WebSocket).
        
        Args:
            messages: Array of message objects with 'role' and 'content'
            provider: LLM provider (defaults to configured provider)
            model: Model name (defaults to configured model)
            max_tokens: Max tokens in response (defaults to configured value)
            
        Returns:
            LLMResponse with content and metadata
        """
        if self.use_websocket:
            return self.chat_websocket(messages, provider, model, max_tokens)
        else:
            return self.chat_rest(messages, provider, model, max_tokens)
    
    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        provider: str = None,
        model: str = None,
        max_tokens: int = None
    ) -> str:
        """
        Generate text from a prompt (convenience method).
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt
            provider: LLM provider
            model: Model name
            max_tokens: Max tokens in response
            
        Returns:
            Generated text content, or error message if failed
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat(messages, provider, model, max_tokens)
        
        if response.success:
            return response.content
        else:
            return f"Error: {response.error}"
    
    # ==================== Status Methods ====================
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get provider availability and usage statistics from middleware.
        
        Returns:
            Status dictionary with provider information
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/status",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status request failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Cannot get status: {str(e)}"}
    
    def health_check(self) -> bool:
        """
        Check if the middleware server is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def close(self):
        """Clean up resources (close WebSocket if open)"""
        self._close_websocket()


# ==================== Singleton Instance ====================

_llm_client: Optional[LLMMiddlewareClient] = None


def get_llm_client() -> LLMMiddlewareClient:
    """
    Get or create the global LLM middleware client instance.
    
    Returns:
        LLMMiddlewareClient singleton instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMMiddlewareClient()
    return _llm_client


def generate_with_middleware(
    prompt: str,
    system_prompt: str = None,
    provider: str = None,
    model: str = None,
    max_tokens: int = None
) -> str:
    """
    Convenience function to generate text using the LLM middleware.
    
    Args:
        prompt: User prompt text
        system_prompt: Optional system prompt
        provider: LLM provider (openai, google, cerebras, groq)
        model: Model name
        max_tokens: Max tokens in response
        
    Returns:
        Generated text content, or error message if failed
    """
    client = get_llm_client()
    return client.generate(prompt, system_prompt, provider, model, max_tokens)
