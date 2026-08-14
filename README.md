# NIA AI
### *Intelligence for the People. Built for Justice.*

<p align="center">
  <img src="nia.png" width="300" alt="Nia" />
</p>

> **Nia** (Swahili) — *Purpose*

Nia is an open-source AI agent system designed to help disadvantaged communities — with a particular focus on Black Americans and people of color — navigate the systems that too often work against them: **healthcare, housing, employment, education, immigration, and economic opportunity**.

She was built because access to information, legal resources, and advocacy tools should not depend on your zip code, your income, or your skin color.

Built by **Brian Thomas** at **Anthos Intelligence**.

---

## THE PROBLEM

In the United States today:

- Black women die in childbirth at **3x the rate** of white women
- Federal DEI protections are being **systematically dismantled**
- Mass deportations are separating families with **no legal pathway** to fight back
- The racial wealth gap is **wider** than it was in 1968
- Workers, tenants, and students of color face discrimination daily with **no idea how to fight it**

Access to information that could change this sits behind paywalls, legal jargon, and systems designed to be inaccessible to the people who need them most. **Nia closes that gap.**

---

## WHAT NIA DOES

Nia is a multi-agent system: a Chief of Staff agent (Nia) runs intake, triage, and final synthesis, leading a specialized squad:

| Agent | Role |
|-------|------|
| **Nia** | Chief of Staff — intake, triage, final synthesis |
| **Keisha** | Community Liaison — empathetic front-line support, de-escalation |
| **Pamela** | Policy & Documentation — plain-language rights guides |
| **Mike** | Research & Intelligence — policy threats, legislation, court decisions |
| **David** | Legal Navigator — legal hooks, deadlines, attorney-ready documentation |
| **Kelly** | Economic Empowerment — benefits, wage theft, small business |

Together they help people understand their **rights** in plain language, **document situations** for attorneys and advocates, find **real organizations** to call (free or low-cost), and know what to do when ICE shows up, when a hospital dismisses them, when a landlord discriminates.

**Privacy is enforced in code:** zero data retention by default, and immigration situations never touch disk or any cloud API. See [PRIVACY_POLICY.md](PRIVACY_POLICY.md).

---

## QUICK START

**The mission system** (works even with no model installed):

```bash
git clone https://github.com/TushaeBXN/nia-ai
cd nia-ai

# With the local Nia model (privacy-first — requires Ollama)
bash setup.sh              # builds the 'nia' model from the Modelfile
python3 -m nia.cli

# With the Claude API instead
export ANTHROPIC_API_KEY=your_key_here
python3 -m nia.cli --model claude

# No model at all — rights info, legal hooks, and resources still work
python3 -m nia.cli --no-model
```

**Standalone tools:**

```bash
python3 -m tools.resource_router housing      # who can help, by domain
python3 -m tools.document_generator           # build an attorney-ready summary
python3 -m tests.test_runner                  # offline test suite
```

**Just the persona chat** (the original Minister of Verdicts experience):

```bash
python3 chat_nia.py        # or: ollama run nia
```

---

## DOCUMENTATION

| Document | Description |
|----------|-------------|
| [Mission Charter](MISSION_CHARTER.md) | Why Nia exists. The values that govern everything. |
| [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) | How to build Nia — phase by phase, for any capacity level |
| [Technical Specification](TECHNICAL_SPEC.md) | Architecture, agent implementation, privacy spec |
| [Project Status](STATUS.md) | What's built, what's next, audit against the roadmap |
| [Privacy Policy](PRIVACY_POLICY.md) | Plain-language privacy commitments. No exceptions. |
| [Contributing](CONTRIBUTING.md) | How developers, advocates, and lawyers can help |
| [Training Story](TRAINING.md) | How the Nia model was fine-tuned (AI-assisted, on cloud GPUs) |

---

## PROJECT STRUCTURE

```
nia-ai/
├── nia/                     # Core package: CLI, model clients, privacy enforcement
├── agents/                  # The squad — each with a SOUL.md persona + agent.py
│   ├── nia/                 #   Chief of Staff: intake.py, triage.py, verdict.py
│   ├── keisha/ pamela/ mike/ david/ kelly/
├── knowledge/
│   ├── rights/federal/      # Plain-language know-your-rights guides (6th-grade level)
│   └── resources/national/  # Directory of real organizations (JSON)
├── coordination/            # File-based squad coordination + protocols
├── tools/                   # resource_router, document_generator
├── tests/                   # Real-world scenarios + offline test runner
│
├── Modelfile                # Nia's persona layer for Ollama
├── chat_nia.py              # Streaming persona chat
├── generate_nia_data.py     # Persona-hardening training data (free, local)
├── train_nia*.py            # LoRA fine-tuning (GPU)
└── export_nia.sh            # Export trained model to Ollama format
```

---

## NIA'S VOICE

Nia carries two registers, and she knows when each belongs. A person who
needs help gets **the Navigator**: warm, plain, judgment-free. Bad-faith
noise gets **the Minister of Verdicts** — the persona in the weights,
trained on curated Black history and culture:

> *"I do not answer questions. I issue depositions."*

She filters bad-faith premises as **Noise** and redirects to **Signal**:
the historical record, documented disparities, receipts. The persona was
fine-tuned into a 7B model with 12,000+ persona-hardening pairs and
30,000+ curated subject-matter records — not prompt engineering.
[Read the training story →](TRAINING.md)

---

## CORE PRINCIPLES

1. **People First** — Every feature must make a real difference in a real person's life
2. **Radical Accessibility** — Usable at a 6th-grade reading level on a slow, old phone
3. **Privacy as Protection** — For many users, privacy is a safety issue. Zero retention by default.
4. **Community Accountability** — Governed by the communities served, not investors
5. **Intersectional by Design** — Built for people navigating overlapping systems of oppression

---

## BUILT BY

**Brian Thomas (Tushae)**
Founder, Anthos Intelligence Company

---

## LICENSE

MIT (transitioning to a Community Benefit Open Source license — see roadmap)

---

*"The arc of the moral universe is long, but it bends toward justice — when people with tools bend it."*

**Nia AI | Anthos Intelligence Company**
*Built for Everyone. Starting with Those Left Out.*
