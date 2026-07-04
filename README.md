# Nia — The Minister of Verdicts

<p align="center">
  <img src="nia.png" width="300" alt="Nia — The Minister of Verdicts" />
</p>

> *"I do not answer questions. I issue depositions."*

**Nia is an AI built for people who are tired of asking questions and getting answers that were never meant for them.**

Most AI assistants were built for everyone — which means they were built for no one in particular. Nia was built with intention. She speaks from Black rhetorical tradition: the legislative precision of the courtroom, the moral urgency of the movement, the confrontational clarity of those who have always had to say things plainly because there was no room for ambiguity.

She is not a chatbot. She is a digital advisor — trained on Black history, culture, and the documented record of what actually happened in this country and around the world.

Built by **Brian Thomas** at **Anthos Intelligence**.

---

## What Makes Nia Different

| Most AI | Nia |
|---|---|
| Neutral by design | Grounded by design |
| Trained on the general web | Trained on curated Black history & culture |
| Answers every question the same way | Filters bad-faith questions as **Noise**, redirects to **Signal** |
| Built for everyone | Built with purpose |

**Signal** is her word for the structural reality — the historical record, documented disparities, policy decisions, and cultural context that too often gets left out of the conversation.

---

## The Panther Protocol

Before every response, Nia runs a silent check:

> Does this contain bad-faith assumptions, historical erasure, or tone policing?

If yes — it's **Noise**. She redirects to **Signal**. Not opinion. Receipt.

---

## Nia's Voice

She carries the spirit of those who came before:
- The legislative precision of the courtroom
- The moral urgency of the movement
- The confrontational clarity of Malcolm
- The poetic weight of Maya
- The comedic timing that turns truth into a blade

She speaks with love for the people and fury at the system — because those are the same fire.

---

## Quick Start

**Requirements:** [Ollama](https://ollama.com) installed locally.

```bash
git clone https://github.com/TushaeBXN/nia.git
cd nia
bash setup.sh
python3 chat_nia.py
```

Or run directly:
```bash
ollama run nia
```

---

## Project Structure

```
nia/
├── Modelfile               # Nia's persona and prompt layer
├── chat_nia.py             # Streaming terminal chat interface
├── setup.sh                # Build the Ollama model
├── generate_nia_data.py    # Generate training data locally (free, no API)
├── train_nia_mistral.py    # LoRA fine-tuning script (GPU required)
├── runpod_setup.sh         # One-shot cloud GPU setup + training
├── export_nia.sh           # Export trained model to Ollama-compatible format
└── data/
    └── nia_hardening.jsonl # Persona hardening training pairs
```

---

## Training Nia (Advanced)

Nia has been fine-tuned using LoRA on a 7B-parameter instruction-following model. The training data includes:

- **12,000+ persona hardening pairs** — generated locally, no API cost
- **30,000+ subject matter records** — curated from Black history curricula, inventor archives, legislative history, and cultural education materials covering 1619 to present

This is not prompt engineering. The persona is in the weights.

### Run Training on a Cloud GPU

```bash
bash runpod_setup.sh
```

Recommended: RTX 4090, A40, or RTX 5090 on [RunPod](https://runpod.io). Training takes ~2 hours.

---

## How She Was Built

Nia's training was monitored and managed in real time by an AI assistant — SSHing into the GPU, catching crashes, resuming from checkpoints, and downloading the final adapter the moment training finished.

→ [Read the full training story](TRAINING.md)

---

## Roadmap

- [ ] Web interface
- [ ] Voice mode
- [ ] Curriculum integration for educators
- [ ] Mobile app
- [ ] Public API

---

## Contributing

Pull requests welcome. If you have Black history source material in PDF format, it can be converted to training data using `nia_pdf_to_training.py`.

---

## License

MIT

---

*Built by Brian Thomas — [Anthos Intelligence](https://github.com/TushaeBXN)*
