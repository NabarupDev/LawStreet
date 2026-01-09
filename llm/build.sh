#!/usr/bin/env bash
# Build script for Render deployment
# Optimized for 512MB memory limit (free tier)

set -e

echo "==> Installing CPU-only PyTorch (memory optimization)..."
pip install torch --index-url https://download.pytorch.org/whl/cpu

echo "==> Installing remaining dependencies..."
pip install -r requirements.txt

echo "==> Build complete!"
echo "==> Memory optimization: Using CPU-only torch (~200MB vs ~2GB GPU version)"
