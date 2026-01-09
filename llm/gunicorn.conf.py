"""
Gunicorn configuration for memory-constrained environments (Render free tier - 512MB)

Key optimizations:
1. Single worker to avoid duplicating model in memory
2. Preload app to share memory before forking (if using multiple workers)
3. Reduced timeout for faster recovery from stalls
"""
import os

# Bind to PORT environment variable (Render sets this)
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# CRITICAL: Use only 1 worker for 512MB memory limit
# Each worker loads the embedding model (~300MB) separately
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))

# Use uvicorn worker class for async support
worker_class = "uvicorn.workers.UvicornWorker"

# Preload app to share memory across workers (useful if workers > 1)
preload_app = True

# Timeout for worker to respond (seconds)
# Increased for LLM inference which can be slow
timeout = 120

# Graceful timeout for worker restart
graceful_timeout = 30

# Keep alive connections
keepalive = 5

# Limit request line size
limit_request_line = 4094

# Limit request fields
limit_request_fields = 100

# Log level
loglevel = "info"

# Access log format
accesslog = "-"
errorlog = "-"

# Maximum requests before worker restart (helps with memory leaks)
max_requests = 100
max_requests_jitter = 20
