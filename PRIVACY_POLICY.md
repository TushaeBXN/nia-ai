# Nia Privacy Policy
**Plain language. No exceptions.**
**Last Updated:** 2026-08-14
**Version:** 1.0

---

For many of the people Nia serves, privacy is not a preference — it is safety.
This policy is short on purpose. Plain language, no legal cover.

---

## The Short Version

Your conversations stay on your machine. Nia does not report to anyone.
Brian does not see your conversations. Anthos Intelligence does not see your conversations.
There is no server collecting anything.

---

## What Nia Stores (Local Memory)

If you use `chat_nia.py`, Nia keeps a local memory database (`nia_memory.db`) on **your own machine**. This is what lets her remember your situation across sessions so you never have to repeat yourself.

What goes in:
- Things you tell her about your situation
- Facts she learns about you over time
- Goals and follow-up items you set together

What does NOT go in:
- Your full name, Social Security Number, account numbers, or medical records — if you type them, they are not stored in the memory layer
- Anything from your system or files you did not explicitly share

This database **never leaves your machine**. It is a file in the same folder as Nia. You can delete it at any time by deleting `nia_memory.db` — Nia starts fresh.

---

## Local-First by Design

Nia runs on a model on **your own machine** via [Ollama](https://ollama.com) by default.
In that mode, your words never touch a server — there is no account, no upload, and nothing to intercept.

If you choose to run Nia with a cloud model (`--model claude`), your input is sent to that provider's API and **their data policy applies**. Nia will tell you this at startup. You are always in control of which mode you use.

---

## What Nia Does Not Do

- **No tracking.** No analytics, no usage stats, no third-party scripts.
- **No data sales.** Your conversations are not a product.
- **No sharing.** Nothing is sent to any government agency, corporation, or partner — because nothing is stored to send.
- **No advertising.** Ever.

---

## Your Documents Belong to You

When Nia helps you organize your situation, build a summary, or draft something — that output is displayed on your screen. Nia does not keep a copy. What you save, and where, is entirely your choice.

If you are in a sensitive situation, avoid saving documents on shared, work, or monitored devices.

---

## Questions or Problems

Open an issue at [github.com/TushaeBXN/nia-ai](https://github.com/TushaeBXN/nia-ai).
A privacy gap is a critical bug and gets fixed before anything else.
