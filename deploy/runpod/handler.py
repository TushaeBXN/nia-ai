"""
RunPod Serverless handler for Nia.

Loads TushaeBXN/nia (LoRA adapter) on top of Mistral-7B-Instruct-v0.3
at container startup. Inference runs on GPU via transformers + peft.

Input:  {"message": "My landlord won't fix my heat..."}
Output: {"reply": "...", "domain": "housing", "urgency": "crisis", ...}
"""
import os
import sys
import time

sys.path.insert(0, "/app")
os.environ.setdefault("NIA_SHARED_DIR", "/tmp/nia-shared")

import torch
import runpod
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from peft import PeftModel

from agents.nia.intake import IntakeClassifier, Domain, Urgency
from nia import privacy


BASE_MODEL  = "mistralai/Mistral-7B-Instruct-v0.3"
ADAPTER     = "TushaeBXN/nia"
HF_TOKEN    = os.environ.get("HF_TOKEN")          # set in RunPod secrets
MAX_TOKENS  = int(os.environ.get("NIA_MAX_TOKENS", "512"))
TEMPERATURE = float(os.environ.get("NIA_TEMPERATURE", "0.85"))
TOP_P       = float(os.environ.get("NIA_TOP_P", "0.95"))


# ── Load model at startup (once per container) ────────────────────────────────

print("[Nia] Loading tokenizer...", flush=True)
tokenizer = AutoTokenizer.from_pretrained(
    BASE_MODEL, token=HF_TOKEN, use_fast=True
)

print("[Nia] Loading base model in 4-bit...", flush=True)
from transformers import BitsAndBytesConfig
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)
base = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=bnb_config,
    device_map="auto",
    token=HF_TOKEN,
)

print("[Nia] Applying LoRA adapter...", flush=True)
model = PeftModel.from_pretrained(base, ADAPTER, token=HF_TOKEN)
model.eval()

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=MAX_TOKENS,
    temperature=TEMPERATURE,
    top_p=TOP_P,
    do_sample=True,
    repetition_penalty=1.1,
)

classifier = IntakeClassifier()
print("[Nia] Ready.", flush=True)


# ── Job handler ───────────────────────────────────────────────────────────────

def handler(job: dict) -> dict:
    job_input = job.get("input", {})
    message = (job_input.get("message") or "").strip()

    if not message:
        return {"error": "message is required"}

    privacy.scrub_shared_dir()

    try:
        situation = classifier.classify(message)

        tags = [situation.domain.value]
        if situation.urgency == Urgency.CRISIS:
            tags.append("CRISIS")
        if situation.domain == Domain.IMMIGRATION:
            tags.append("max-privacy")

        messages = [{"role": "user", "content": message}]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        result = pipe(prompt)
        reply = result[0]["generated_text"][len(prompt):].strip()

        return {
            "reply": reply,
            "domain": situation.domain.value,
            "urgency": situation.urgency.value,
            "tags": tags,
            "crisis": situation.urgency == Urgency.CRISIS,
            "immigration": situation.domain == Domain.IMMIGRATION,
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        privacy.scrub_shared_dir()


runpod.serverless.start({"handler": handler})
