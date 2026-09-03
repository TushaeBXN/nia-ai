"""
Pamela — Policy & Documentation
Surfaces the plain-language rights guide for the situation's domain
from knowledge/rights/, with time limits front and center.
"""

import re

from agents.common import speak
from agents.nia.intake import Domain
from nia import config

# Domain → federal rights guide in knowledge/rights/federal/
RIGHTS_DOCS = {
    Domain.HOUSING: "fair_housing_act.md",
    Domain.EMPLOYMENT: "title_vii.md",
    Domain.DISCRIMINATION: "title_vii.md",
    Domain.HEALTHCARE: "maternal_health.md",
}


def _extract_section(text: str, heading: str) -> str:
    """Pull one '## heading' section out of a rights doc."""
    pattern = rf"^## {re.escape(heading)}.*?\n(.*?)(?=^## |\Z)"
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


class Agent:
    def __init__(self, model=None):
        self.model = model

    def handle(self, situation) -> str:
        doc_name = RIGHTS_DOCS.get(situation.domain)
        if not doc_name:
            default = (
                f"I don't have a plain-language rights guide written for "
                f"{situation.domain.value} yet — it's on the roadmap. David's "
                f"legal hooks and Kelly's resources below still apply, and any "
                f"organization in the resources list can explain your rights "
                f"in this area."
            )
            return speak(self.model, "pamela", situation.summary, default)

        doc_path = config.RIGHTS_DIR / "federal" / doc_name
        if not doc_path.exists():
            return f"[Rights guide {doc_name} is missing from the knowledge base.]"

        text = doc_path.read_text()
        title = text.splitlines()[0].lstrip("# ").strip()
        what = _extract_section(text, "What Is It?") or _extract_section(text, "What Are Your Rights?")
        actions = _extract_section(text, "What Can You Do?")
        limits = _extract_section(text, "Time Limits — IMPORTANT")

        parts = [f"YOUR RIGHTS — {title}", ""]
        if what:
            parts += [what, ""]
        if actions:
            parts += ["WHAT YOU CAN DO:", actions, ""]
        if limits:
            parts += ["⏰ TIME LIMITS — DO NOT WAIT:", limits, ""]
        parts.append(f"(Full plain-language guide: knowledge/rights/federal/{doc_name})")
        default = "\n".join(parts)

        return speak(
            self.model,
            "pamela",
            f"Situation: {situation.summary}",
            default,
        )
