# NIA AI — PROJECT STATUS
**Audit Date:** 2026-07-14
**Audited Against:** IMPLEMENTATION_ROADMAP.md v1.0 / TECHNICAL_SPEC.md v1.0

This document maps what exists in this repository against the roadmap phases,
what was added in the Phase 1 build pass, and where the code and the
documentation disagreed (and how each conflict was resolved).

---

## WHAT EXISTED BEFORE THIS PASS

The repo was Nia's **training pipeline and persona layer** — the model, not
the mission system:

| Component | File(s) | State |
|---|---|---|
| Persona / prompt layer | `Modelfile` | Working. "Minister of Verdicts" persona, Panther Protocol, tone system. Base: `llama3.2:3b` |
| Terminal chat | `chat_nia.py` | Working. Stdlib-only streaming client against local Ollama |
| Model build | `setup.sh` | Working. `ollama create nia -f Modelfile` |
| Persona hardening data | `generate_nia_data.py`, `data/nia_hardening.jsonl` | Working. 12k+ pairs, no API cost |
| PDF → training data | `pdf_to_training.py`, `nia_build_dataset.py` | Working. Dedup across files, resumable |
| LoRA training | `train_nia.py`, `train_nia_mistral.py`, `runpod_setup.sh` | Working. Fine-tuned 7B adapter exists (see TRAINING.md) |
| GGUF export | `export_nia.sh` | Working |

**None** of the mission-system structure from TECHNICAL_SPEC.md existed:
no `agents/`, no `knowledge/`, no `tools/`, no `coordination/`, no `tests/`,
no intake, no resource directory, no privacy layer.

---

## ROADMAP PHASE STATUS

### Phase 0 — Foundation
- [x] Mission Charter adopted → `MISSION_CHARTER.md` (added this pass)
- [x] Privacy-first data policy → `PRIVACY_POLICY.md` (added this pass)
- [x] Deployment model chosen → **local-first Ollama**, optional Claude API
- [ ] Community context doc (`COMMUNITY_CONTEXT.md`) — needs Brian/community input
- [ ] 3–5 community partners identified (`PARTNER_LIST.md`) — needs human outreach

**Phase 0: ~60% — remaining items are human/community tasks, not code.**

### Phase 1 — Nia Core  ← CURRENT PHASE
- [x] Situation intake — `agents/nia/intake.py` (classifier + urgency + structured Situation)
- [x] Triage / squad routing — `agents/nia/triage.py`
- [x] Verdict synthesis — `agents/nia/verdict.py`
- [x] Working core agent, CLI — `python -m nia.cli`
- [x] Know-your-rights engine started — `knowledge/rights/federal/` (maternal health, FHA, Title VII)
- [x] Situation documenter — `tools/document_generator.py`
- [x] Resource router — `tools/resource_router.py` + `knowledge/resources/national/` (20+ orgs)
- [x] SOUL.md finalized and loaded — `agents/nia/SOUL.md`
- [ ] National directory at 50+ organizations (currently 20+; grow to 50)
- [ ] Rights docs for remaining domains (education, immigration, economic, ADA)
- [ ] Legal-professional review of all rights content (**required before deployment**)

**Phase 1: core capabilities built; content expansion + legal review remain.**

### Phase 2 — The Squad
- [x] SOUL.md persona files for all six agents — `agents/*/SOUL.md`
- [x] Squad agent scaffolds with `handle(situation)` — `agents/*/agent.py`
- [x] File-based coordination protocol — `coordination/`
- [ ] Mike's automated monitors (`federal_register.py`, bill trackers) — not built
- [ ] Domain knowledge bases per agent — only federal rights docs so far
- [ ] Community scenario testing with real users

### Phases 3–6 (Localization, Deep Domain Tools, Governance, Scale)
Not started. Test scenarios for Phase 4 domains are in `tests/scenarios/`.

### Policy tracker + training series (added 2026-07-14)
- `knowledge/policy_tracker/` — Project 2025 institutional map, policy impact
  matrix, external network index, and `active_threats.md` (implementation
  status verified July 2026). This is the knowledge base Mike's Phase 2
  monitors will keep current.
- `training/` — schematic for a 4-module community training PDF series
  ("Navigating the New Federal Landscape"). Needs legal/benefits-professional
  review before distribution, same as the rights docs.

---

## CONFLICTS FOUND (AND RESOLUTIONS)

1. **`~/nia-squad/` does not exist on this machine.** The build brief describes
   a squad already coordinating via `~/nia-squad/agents/[name]/SOUL.md`. No such
   directory exists locally. **Resolution:** the squad structure was created
   *inside this repo* (`agents/`, `coordination/`) per TECHNICAL_SPEC.md so it is
   versioned and shippable. If a `~/nia-squad/` exists on another machine, its
   SOUL.md files should be diffed against these and merged — `nia/config.py`
   honors a `NIA_SQUAD_DIR` env var so an external squad dir can be pointed at.

2. **Two personas: "Minister of Verdicts" (Modelfile) vs. warm navigator
   (roadmap SOUL template).** The Modelfile persona is confrontational by
   design; the roadmap's Nia "never lectures" and leads with warmth.
   **Resolution:** conditional tone-switching, made explicit in
   `agents/nia/SOUL.md` — a person in crisis gets the navigator (warm, plain,
   practical); bad-faith noise gets the Verdicts register. The Modelfile is
   untouched: it remains the personality layer for `ollama run nia` /
   `chat_nia.py`. The mission system loads SOUL.md files instead.

3. **Base model mismatch in docs.** README says fine-tuned 7B; `Modelfile`
   says `FROM llama3.2:3b`; TRAINING.md says the LoRA is Mistral-7B at
   `checkpoints/nia-mistral-lora/checkpoint-6000` (not in repo — gitignored).
   **Resolution:** left as-is; noted so nobody is surprised. The mission system
   is model-agnostic (`nia/model.py` takes any Ollama model name).

4. **Spec quickstart says `python -m nia.cli` but the spec file tree has no
   `nia/` package.** **Resolution:** added a thin `nia/` package (cli, model
   client, config, privacy) alongside the spec's `agents/` tree so the
   documented command works.

5. **TECHNICAL_SPEC's `NiaAgent._parse_situation` calls `json.loads` on raw
   model output** — small local models frequently wrap JSON in prose or
   fences, and this repo's target hardware is modest. **Resolution:**
   `intake.py` extracts the first JSON object defensively and falls back to a
   deterministic keyword classifier, so intake **never crashes and works even
   with no model running**. That fallback is also what `tests/test_runner.py`
   exercises offline.

6. **Old README quickstart pointed at `github.com/TushaeBXN/nia.git`** while
   this repo is `nia-ai`. Fixed in README.

---

## PRIVACY POSTURE (Priority 6)

- Zero retention by default: coordination case files are wiped at session end
  (`nia/privacy.py`), and `coordination/shared/` is gitignored so case data
  can never be committed.
- Immigration interactions run in **maximum privacy mode**: nothing is written
  to disk at any point — coordination happens in memory only, no logs.
- No web interface exists in this repo, therefore **no third-party scripts or
  analytics anywhere** — confirmed by audit. (The separate `nia-site` static
  pages are outside this repo; audit them before linking them to Nia.)

---

## IMMEDIATE NEXT STEPS

1. Grow national resource directory 20 → 50 orgs; verify every phone/URL.
2. Add remaining federal rights docs (immigration/ICE encounters next —
   pairs with max-privacy mode).
3. Get a legal aid partner to review the three rights docs (spec requires
   review before deployment).
4. Wire the fine-tuned Nia model into `nia/model.py` end-to-end and run the
   four spec scenarios against the live model.
5. Build Mike's Federal Register monitor (first Phase 2 automation).
