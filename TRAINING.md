# How Nia Was Trained

This documents the real process behind Nia's LoRA fine-tuning — including what broke, how it was fixed, and what made this build different.

---

## The Setup

Nia was trained on a cloud GPU (NVIDIA RTX 5090, 32GB VRAM) via [RunPod](https://runpod.io). The base model is a 7B-parameter instruction-following model fine-tuned with LoRA (Low-Rank Adaptation) — meaning only a small adapter layer (~160MB) was trained on top of frozen base weights.

Training data: **32,000+ records** spanning:
- Persona hardening pairs (who Nia is, how she speaks, what she refuses)
- Black history curricula from 1619 to present
- Inventor archives, leadership profiles, legislative history, cultural education PDFs

---

## AI-Assisted Training Pipeline

What made this build unique: **Claude Code (AI) monitored and managed the entire training run in real time.**

Rather than a human babysitting the GPU, Claude Code:

- SSHed into the RunPod instance directly
- Polled training logs every minute, reporting step progress
- Detected when the session froze and diagnosed the cause
- Resumed training from the last saved checkpoint automatically
- Caught and fixed a CUDA out-of-memory error mid-run (dropped batch size, enabled `expandable_segments`)
- Downloaded the final adapter the moment training completed
- Verified the checkpoint landed locally before the pod was stopped

This is AI building AI — the same intelligence Nia is built on helped construct her.

---

## What Went Wrong (and How We Fixed It)

### Session freeze
The first pod froze mid-training at step 5000 of 6340. The pod was still alive. Claude Code SSHed in, confirmed the process had died, found the last checkpoint, and relaunched from there.

### Out of memory (OOM)
On the second pod (new GPU), training crashed with a CUDA OOM error. Fix: reduced batch size from 4 → 1, increased gradient accumulation from 4 → 16, and set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. Training resumed cleanly.

### Missing training script
The original `train_nia_8b.py` only existed on the first pod, which was gone. Claude Code reconstructed the script from the checkpoint's `adapter_config.json`, identified the correct base model, and rewrote the trainer to handle both `messages` and `system/instruction/response` data formats.

### Budget pressure
With $1.42 remaining and hours of training left, the decision was made to download checkpoint-5000 as a safety copy, spin up a new pod with a persistent network volume, and finish the remaining 1,340 steps on fresh hardware.

---

## Final Checkpoint

- **Steps completed:** 6,340
- **Adapter size:** ~160MB
- **Format:** PEFT LoRA (`.safetensors`)
- **Location:** `checkpoints/nia-mistral-lora/checkpoint-6000`

---

## Lessons

- Always use a **network volume** on RunPod — pod storage dies with the pod
- Save checkpoints frequently (`save_steps=400`)
- AI-assisted monitoring is a legitimate training workflow — not a gimmick
- The model that helped build Nia is the same class of model Nia aspires to surpass for her community

---

*Built by Brian Thomas — Anthos Intelligence*
