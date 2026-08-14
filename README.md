# NIA AI
### *Intelligence for the People. Built for Justice.*

<p align="center">
  <img src="nia.png" width="300" alt="Nia" />
</p>

> **Nia** (Swahili) — *Purpose*

Nia is an open-source AI assistant built to help underserved communities — Black Americans, Native Americans, poor working families, and the global African diaspora — navigate systems that were never designed with them in mind: **healthcare, housing, employment, education, and economic opportunity**.

She was built because access to information and the tools to act on it should not depend on your zip code, your income, or your skin color.

Built by **Brian Thomas** at **Anthos Intelligence**.

---

## THE PROBLEM

In the United States today:

- Black mothers experience significantly higher rates of complications during childbirth than their peers — a gap that persists across income levels
- Workplace and housing protections that took decades to build are being quietly rolled back
- Families across this country are being separated by policies that move faster than anyone can respond to
- The wealth gap between Black and white Americans has barely moved in over fifty years — and in some measures has grown
- Millions of people are navigating healthcare denials, housing disputes, and job losses every day with no idea what options they have

The information that could change outcomes exists. But it sits behind paywalls, jargon, and systems built to be hard to reach. **Nia closes that gap.**

---

## WHAT NIA DOES

Nia is a multi-agent AI system built around specialized areas of focus:

| Area | What It Covers |
|------|----------------|
| **Community Support** | Front-line help, emotional grounding, connecting people to real resources |
| **Research & Intelligence** | Current policy changes, community impact analysis, what's actually happening |
| **Economic Empowerment** | Benefits navigation, small business, wealth-building strategies |
| **Documentation** | Plain-language guides, situation summaries, organized records |

Together, these capabilities help people understand their options in plain language, find **real organizations** to call (free or low-cost), and take action when a hospital dismisses them, a landlord won't respond, or a job opportunity falls through.

**Privacy is built in:** zero data retention by default. What you share stays local. See [PRIVACY_POLICY.md](PRIVACY_POLICY.md).

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

# No model at all — guides and resources still work
python3 -m nia.cli --no-model
```

**Standalone tools:**

```bash
python3 -m tools.resource_router housing      # find resources by domain
python3 -m tools.document_generator           # build a situation summary
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
| [Contributing](CONTRIBUTING.md) | How developers and advocates can help |
| [Training Story](TRAINING.md) | How the Nia model was fine-tuned (AI-assisted, on cloud GPUs) |

---

## PROJECT STRUCTURE

```
nia-ai/
├── nia/                     # Core package: CLI, model clients, privacy enforcement
├── agents/                  # Specialized agents by focus area
├── knowledge/
│   ├── rights/federal/      # Plain-language guides (6th-grade reading level)
│   └── resources/national/  # Directory of real organizations (JSON)
├── coordination/            # Agent coordination protocols
├── tools/                   # resource_router, document_generator
├── tests/                   # Scenario-based offline test suite
│
├── Modelfile                # Nia's persona layer for Ollama
├── chat_nia.py              # Full companion chat (voice, memory, tools)
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
