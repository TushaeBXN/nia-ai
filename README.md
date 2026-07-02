# Nia — The Minister of Verdicts

> *"I do not answer questions. I issue depositions."*

Nia is a custom AI persona built on Black rhetorical tradition. She speaks with the legislative precision of Jasmine Crockett, the moral urgency of Dr. King, the confrontational clarity of Malcolm X, the comedic timing of Katt Williams, and the poetic devastation of Maya Angelou.

She operates on the **Panther Protocol** — every response is checked against the spirit of the 1966 Ten-Point Program before it is issued.

Built by **Brian Thomas**.

---

## What Nia Is

Nia is not a chatbot. She is a digital war room. She:

- Does not debate the existence of systemic racism — she cites the record
- Flags bad-faith questions as **Noise** and redirects to **Signal**
- Refuses tone policing — clarity is not aggression
- Connects users to mutual aid, police budget auditing, documentation of human rights abuses, and indigenous land-back movements
- Speaks with love for the people and fury at the system — these are the same fire

---

## Project Structure

```
nia/
├── Modelfile               # Ollama model definition (prompt-layer Nia)
├── chat_nia.py             # Streaming terminal chat interface
├── setup.sh                # Build / rebuild the Ollama model
├── generate_nia_data.py    # Generate 10k+ hardening training pairs (no API, no cost)
├── train_nia.py            # LoRA fine-tune on RunPod / Colab
├── runpod_setup.sh         # One-shot RunPod setup + training script
├── export_nia.sh           # Merge adapter → GGUF → Q4_K_M for Ollama
└── data/
    └── nia_hardening.jsonl # 12k generated training pairs
```

---

## Quick Start (Ollama — no training required)

```bash
# Build Nia in Ollama (uses llama3.2:3b as base)
bash setup.sh

# Chat
python3 chat_nia.py

# Or directly
ollama run nia
```

Requires [Ollama](https://ollama.com) with `llama3.2:3b` pulled.

---

## Harden Nia (LoRA Fine-Tuning)

Hardening burns the persona into the model weights — Nia speaks in her voice without needing the system prompt.

### Step 1 — Generate training data (local, free)

```bash
python3 generate_nia_data.py --n 12000 --out data/nia_hardening.jsonl
```

Produces 12,000 training pairs across five categories:

| Category | Count | Purpose |
|---|---|---|
| Identity | ~3,000 | Who Nia is, who built her |
| Noise/bad-faith deflection | ~2,400 | Panther Protocol in action |
| Tone policing responses | ~1,200 | No softening |
| Refusal deflections | ~1,200 | She cannot be made neutral |
| Strategy & history | ~4,200 | What Nia teaches |

### Step 2 — Train on RunPod

Upload this repo to a RunPod instance (RTX 4090 or A40 recommended), then:

```bash
bash runpod_setup.sh
```

This installs dependencies, generates data, and runs LoRA training on `meta-llama/Llama-3.2-3B-Instruct`.

### Step 3 — Export to Ollama

```bash
bash export_nia.sh
```

Merges the adapter into the base model, converts to GGUF, and quantizes to Q4_K_M (~2GB). Download the GGUF file and load it into Ollama locally.

---

## The Panther Protocol

Before generating any response, Nia runs a silent internal check:

> Does this question contain bad-faith assumptions, historical erasure, tone policing, or the centering of oppressor comfort over oppressed survival?

If yes — it is **Noise**. She pivots to **Signal**.

Signal is the structural reality: the historical record, the documented disparities, the policy decisions that built inequality. Not opinion. Receipt.

---

## Base Model

- **Prompt layer**: `llama3.2:3b` via Ollama
- **LoRA hardening target**: `meta-llama/Llama-3.2-3B-Instruct`

---

*Built by Brian Thomas.*
