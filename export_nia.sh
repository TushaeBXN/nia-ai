#!/bin/bash
# Merge LoRA adapter into base model and export to GGUF for Ollama
# Run this on RunPod after training completes

set -e

ADAPTER="checkpoints/nia-lora"
MERGED="checkpoints/nia-merged"
GGUF="checkpoints/nia-q4.gguf"

echo "=== Nia Export Pipeline ==="

# Step 1: Merge adapter into base model
echo "Merging LoRA adapter into base model..."
python - <<'EOF'
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

base = "meta-llama/Llama-3.2-3B-Instruct"
adapter = "checkpoints/nia-lora"
output = "checkpoints/nia-merged"

print(f"Loading {base}...")
tokenizer = AutoTokenizer.from_pretrained(base)
model = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.float16, device_map="auto")

print("Applying adapter...")
model = PeftModel.from_pretrained(model, adapter)
model = model.merge_and_unload()

print(f"Saving merged model to {output}...")
model.save_pretrained(output)
tokenizer.save_pretrained(output)
print("Merge complete.")
EOF

# Step 2: Convert to GGUF using llama.cpp
echo ""
echo "Converting to GGUF..."

if [ ! -d "llama.cpp" ]; then
    echo "Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp --depth 1
    cd llama.cpp && pip install -r requirements.txt && cd ..
fi

python llama.cpp/convert_hf_to_gguf.py \
    checkpoints/nia-merged \
    --outfile checkpoints/nia-f16.gguf \
    --outtype f16

# Step 3: Quantize to Q4_K_M
echo "Quantizing to Q4_K_M (~2GB)..."
llama.cpp/llama-quantize checkpoints/nia-f16.gguf $GGUF Q4_K_M

echo ""
echo "=== Export complete ==="
echo "GGUF: $GGUF"
echo ""
echo "Download this file to your Mac, then run:"
echo "  ollama create nia-hardened -f Modelfile.hardened"
echo ""
echo "Create Modelfile.hardened with:"
echo "  FROM ./checkpoints/nia-q4.gguf"
echo "  (no SYSTEM block needed — persona is in the weights)"
