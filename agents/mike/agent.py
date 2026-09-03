"""
Mike — Research & Intelligence
Policy context for the situation. Automated monitors (Federal Register,
state bill trackers, court watch) are Phase 2 — until they exist, Mike is
honest about that and gives verified static context only.
"""

from agents.common import speak
from agents.nia.intake import Domain

POLICY_CONTEXT = {
    Domain.EMPLOYMENT: (
        "One thing that matters right now: retaliation is its own violation. "
        "Even while federal enforcement priorities shift, Title VII's "
        "anti-retaliation protections remain law, and retaliation claims are "
        "among the most commonly won at the EEOC. A sudden bad review right "
        "after you raised pay discrimination is a classic pattern — the "
        "timing itself is evidence. Document the sequence of events precisely."
    ),
    Domain.EDUCATION: (
        "Curriculum restrictions vary enormously by state, and districts "
        "often over-comply — banning more than the state law actually "
        "requires. Two questions cut through it: (1) What is the exact bill "
        "number the district is citing? (2) What does its text actually "
        "prohibit? Your state ACLU affiliate tracks these laws and will know."
    ),
    Domain.IMMIGRATION: (
        "Enforcement practices are changing quickly, but constitutional "
        "rights are not: the right to remain silent and the judge-signed "
        "warrant requirement for entering a home have not changed. Local "
        "rapid-response networks track enforcement activity in real time — "
        "the resources list includes hotlines that connect you to them."
    ),
    Domain.HEALTHCARE: (
        "Context worth knowing: Black maternal mortality is about 3x the "
        "white rate, and the CDC found that most pregnancy-related deaths "
        "are preventable. This is documented at the federal level — which "
        "means 'I was dismissed while pregnant' is a recognized, reportable "
        "patient-safety and civil-rights issue, not a personal complaint."
    ),
}

MONITOR_NOTE = (
    "My automated trackers (Federal Register, state legislatures, court "
    "decisions) aren't live yet — that's Phase 2 of the roadmap. For "
    "today's status of any specific law or case, the legal organizations "
    "in the resources list have current information."
)


class Agent:
    def __init__(self, model=None):
        self.model = model

    def handle(self, situation) -> str:
        context = POLICY_CONTEXT.get(situation.domain)
        default = (context + "\n\n" if context else "") + MONITOR_NOTE
        return speak(
            self.model,
            "mike",
            f"Situation: {situation.summary}",
            default,
        )
