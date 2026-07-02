#!/bin/bash
set -e

echo "Building Nia — The Minister of Verdicts..."
echo ""

# Remove old model if it exists
if ollama list | grep -q "^nia"; then
    echo "Removing old nia model..."
    ollama rm nia
fi

# Build from Modelfile
echo "Creating model from Modelfile..."
ollama create nia -f Modelfile

echo ""
echo "✓ Nia is ready."
echo ""
echo "To chat:  python3 chat_nia.py"
echo "Or:       ollama run nia"
