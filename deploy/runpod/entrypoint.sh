#!/bin/bash
# Fix #1 — proper Ollama startup sequence before handler starts
set -e

echo "[Nia] Starting Ollama service..."
ollama serve &

echo "[Nia] Waiting for Ollama to be healthy..."
until curl -sf http://localhost:11434/api/version >/dev/null 2>&1; do
    sleep 1
done
echo "[Nia] Ollama is healthy."

# Model was pre-baked at build time. If for any reason it's missing, recreate it.
if ! ollama list 2>/dev/null | grep -q "^nia "; then
    echo "[Nia] WARNING: nia model not found — recreating from Modelfile..."
    ollama create nia -f /tmp/Modelfile
fi
echo "[Nia] nia model confirmed."

echo "[Nia] Starting serverless handler..."
exec python3 -u /app/handler.py
