"""
Kelly — Economic Empowerment
Benefits navigation, wage documentation, grants, veteran resources,
real estate analysis, and the full economic side of any situation.
"""

from agents.common import speak
from agents.nia.intake import Domain
try:
    from skills import skill_prompt, skills_for_squad, Squad
except ImportError:
    skill_prompt = None
    skills_for_squad = None
    Squad = None

BENEFITS_NOTE = """Money help you may be leaving on the table (millions of people qualify and never apply):
- Dial 211 (or 211.org) — free, confidential, connects you to local help with
  rent, utilities, food, and emergency assistance
- benefits.gov — one screener for SNAP, Medicaid, TANF, WIC, LIHEAP and more
- If a benefit was DENIED or cut off: that decision can be appealed. The
  deadline is on the denial letter — legal aid will handle the appeal free."""

WAGE_NOTE = """If money was taken from you at work (unpaid hours, unpaid overtime, a pay gap):
- Write down every pay period affected and what you were actually paid
- Keep your own copies of pay stubs, schedules, and time records
- The Department of Labor takes wage complaints free and does not ask about
  immigration status: 1-866-487-9243"""

# Keywords that trigger specific economic skills
_SKILL_TRIGGERS = {
    "grant-finder": ["grant", "funding", "money for my", "fund my", "financial support"],
    "veteran-resource-finder": ["veteran", "va benefit", "va program", "military service"],
    "senior-services-mapper": ["senior", "elderly", "aging", "elder", "nursing"],
    "financial-model-builder": ["financial model", "projection", "p&l", "cash flow", "budget", "pro forma"],
    "real-estate-analyzer": ["property", "building", "real estate", "this address", "acre", "zoning"],
}


def _detect_skill(summary: str) -> str | None:
    low = summary.lower()
    for skill, triggers in _SKILL_TRIGGERS.items():
        if any(t in low for t in triggers):
            return skill
    return None


class Agent:
    def __init__(self, model=None):
        self.model = model

    def handle(self, situation) -> str:
        parts = [BENEFITS_NOTE]
        if situation.domain in (Domain.EMPLOYMENT, Domain.ECONOMIC):
            parts.append(WAGE_NOTE)

        # Detect and inject skill guidance when situation matches
        if skill_prompt:
            skill = _detect_skill(situation.summary)
            if skill:
                parts.append(skill_prompt(skill, situation.summary))

        default = "\n\n".join(parts)
        return speak(
            self.model,
            "kelly",
            f"Situation: {situation.summary}",
            default,
        )
