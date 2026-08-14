#!/bin/bash
set -e

echo "Building Nia — The Minister of Verdicts..."
echo ""

# Install Python runtime deps
echo "Installing Python dependencies..."
pip install "ollama>=0.3.0" "numpy<2" "piper-tts>=1.5.0" \
    "ddgs>=7.0.0" "beautifulsoup4>=4.12.0" "requests>=2.31.0" \
    "pymupdf>=1.24.0"

echo ""

# Pull required Ollama models
echo "Pulling Ollama models..."
ollama pull nomic-embed-text

echo ""

# Remove old model if it exists
if ollama list | grep -q "^nia"; then
    echo "Removing old nia model..."
    ollama rm nia
fi

# Build from Modelfile
echo "Creating Nia model..."
ollama create nia -f Modelfile

echo ""

# Download Piper voice if not present
VOICES_DIR="$(dirname "$0")/voices"
VOICE_FILE="$VOICES_DIR/en_US-lessac-high.onnx"
VOICE_JSON="$VOICES_DIR/en_US-lessac-high.onnx.json"

mkdir -p "$VOICES_DIR"

if [ ! -f "$VOICE_FILE" ]; then
    echo "Downloading Piper voice (en_US-lessac-high)..."
    curl -L -o "$VOICE_FILE" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx"
    curl -L -o "$VOICE_JSON" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx.json"
    echo "Voice downloaded."
fi

echo ""

# Whisper setup (optional — for /listen and /converse)
WHISPER_DIR="$(dirname "$0")/whisper-models"
WHISPER_MODEL="$WHISPER_DIR/ggml-base.en.bin"

if [ ! -f "$WHISPER_MODEL" ]; then
    echo "Whisper model not found. To enable voice input:"
    echo "  mkdir -p whisper-models"
    echo "  curl -L -o whisper-models/ggml-base.en.bin \\"
    echo "    https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"
    echo "  brew install whisper-cpp  # or build from source"
fi

echo ""
echo "✓ Nia is ready."
echo ""
echo "To chat:   python3 chat_nia.py"
echo "Or:        ollama run nia"
