"""
Situation Documenter (Phase 1)

Turns Nia's structured Situation into a plain-language summary a person
can hand to a lawyer, advocate, or social worker: chronological facts,
parties involved, actions taken, and potential legal hooks.

Works with no model — the document is assembled from the structured
Situation plus David's verified legal-hooks table. A model, when present,
is used only inside intake (better summaries), never to invent content here.

Usage (interactive):
    python -m tools.document_generator

Or from code:
    from tools.document_generator import generate
    text = generate(situation, parties=[...], actions_taken=[...])
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.david.agent import hooks_for
from agents.nia import intake as intake_module
from agents.nia.intake import Situation

DISCLAIMER = (
    "This summary was prepared by the person named above with help from "
    "Nia, an AI navigation tool. It is a factual account in the person's "
    "own words, organized for intake purposes. It is not legal advice and "
    "was not prepared by an attorney."
)


def _bullets(items, empty="- (none provided)"):
    items = [i.strip() for i in (items or []) if i and i.strip()]
    return "\n".join(f"- {i}" for i in items) if items else empty


def generate(situation: Situation, parties=None, actions_taken=None,
             first_name: str = "the person seeking help") -> str:
    """Build the advocate-handoff document as markdown text."""
    hooks = hooks_for(situation.domain)
    if hooks:
        hooks_text = "\n".join(
            f"- **{h['law']}** — {h['covers']}\n"
            f"  - Where to file: {h['agency']}\n"
            f"  - Time limit: {h['deadline']}"
            for h in hooks
        )
    else:
        hooks_text = "- To be assessed by counsel."

    return f"""# Situation Summary — For Attorney / Advocate Intake
**Prepared:** {date.today().isoformat()}
**Prepared for:** {first_name}
**Domain:** {situation.domain.value}
**Urgency:** {situation.urgency.value}
**State:** {situation.state or "not stated"}

## Summary of the Situation
{situation.summary}

## Chronological Facts (in the person's own words)
{_bullets(situation.documented_facts)}

## Parties Involved
{_bullets(parties, empty="- (to be completed with the person during intake)")}

## Actions Taken So Far
{_bullets(actions_taken, empty="- (none yet — no complaints filed, no agencies contacted)")}

## Potential Legal Hooks (for counsel to assess)
{hooks_text}

## Evidence and Documentation Available
- (List what exists: texts, emails, photos, records, witness names)

---
*{DISCLAIMER}*
"""


def _ask_list(prompt: str) -> list:
    """Collect list items from the terminal until a blank line."""
    print(prompt + " (one per line, blank line to finish)")
    items = []
    while True:
        try:
            line = input("  > ").strip()
        except EOFError:
            break
        if not line:
            break
        items.append(line)
    return items


def main():
    print("Situation Documenter — builds a summary you can hand to a lawyer,")
    print("advocate, or social worker. Nothing you type here is saved by Nia.\n")

    print("Describe what happened, in your own words (blank line to finish):")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip() and lines:
            break
        if line.strip():
            lines.append(line)
    text = " ".join(lines)
    if not text:
        sys.exit(0)

    situation = intake_module.intake(text)  # keyword fallback; no model needed
    parties = _ask_list("\nWho was involved? (names/roles, e.g. 'J. Smith — property manager')")
    actions = _ask_list("\nWhat have you done so far? (calls made, complaints filed)")
    name = input("\nFirst name to put on the document (or press Enter to skip): ").strip()

    doc = generate(situation, parties=parties, actions_taken=actions,
                   first_name=name or "the person seeking help")
    print("\n" + "=" * 70 + "\n")
    print(doc)
    print("=" * 70)
    print("\nCopy the text above, or redirect it to a file yourself if you")
    print("choose to — Nia does not save it. If this involves immigration,")
    print("avoid saving it on a shared or work device.")


if __name__ == "__main__":
    main()
