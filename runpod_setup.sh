#!/bin/bash
# RunPod setup script for Nia LoRA hardening
# Run this inside a RunPod instance after uploading the nia/ directory

set -e

echo "=== Nia RunPod Setup ==="

# Install deps
pip install -q \
    torch \
    transformers \
    peft \
    datasets \
    accelerate \
    bitsandbytes

# Generate training data
echo ""
echo "Generating training data..."
python generate_nia_data.py --n 12000 --out data/nia_hardening.jsonl

# Run training
echo ""
echo "Starting LoRA hardening..."
python train_nia.py \
    --data data/nia_hardening.jsonl \
    --steps 1000 \
    --batch 8 \
    --grad-accum 2

echo ""
echo "=== Hardening complete ==="
echo "Adapter saved to: checkpoints/nia-lora/"
echo ""
echo "To export to GGUF for Ollama, run: bash export_nia.sh"
