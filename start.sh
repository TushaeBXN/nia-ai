#!/bin/bash
# Nia startup launcher — exports Ollama server vars before starting the server,
# then launches the Nia FastAPI server.
set -a
source "$(dirname "$0")/.env"
set +a

echo "[nia] OLLAMA_KEEP_ALIVE=$OLLAMA_KEEP_ALIVE  NUM_PARALLEL=$OLLAMA_NUM_PARALLEL  NUM_THREADS=$OLLAMA_NUM_THREADS"
echo "[nia] Starting server on :3100 ..."
exec python3 nia_server.py
