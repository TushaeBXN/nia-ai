# Handoff Protocol

1. Nia writes `coordination/shared/current_case.md` after intake
   (skipped entirely in maximum privacy mode — handoff happens in memory).
2. Assigned agents read the case and write findings to
   `coordination/shared/<agent>_notes.md`:
   - keisha — emotional support, safety, de-escalation
   - pamela — plain-language rights (from knowledge/rights/)
   - mike — policy context and active threats
   - david — legal hooks, deadlines, documentation checklist
   - kelly — benefits, money, economic next steps
3. The Resource Router appends matched organizations.
4. Nia reads all findings and synthesizes `verdict.md` — one warm,
   plain, actionable response.
5. Session end: every file written in steps 1–4 is deleted.
   `coordination/shared/` is gitignored so case data can never be committed.

Agents never add facts the knowledge base can't back. If a model is used
to phrase findings, it may change voice — never facts, numbers, or laws.
