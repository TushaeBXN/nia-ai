"""
Keisha — Community Liaison
Empathetic front-line intake: emotional support and de-escalation.
"""

from agents.common import speak
from agents.nia.intake import Domain, Urgency


CRISIS_GROUNDING = """First — before anything else:
- If anyone is in immediate physical danger, call 911 now.
- You do not have to handle this alone, and you do not have to handle it all today.
- Take one breath. The next steps below are small on purpose. One at a time."""

IMMIGRATION_SAFETY = """A few things to know right now:
- You have rights no matter your status. You do not have to answer questions
  about where you or anyone else was born, or how anyone entered the country.
- Do not open the door to ICE unless they show a warrant signed by a judge
  (slide it under the door to check — an "ICE warrant" is not enough).
- Nothing you tell me is saved. This conversation leaves no record here."""


class Agent:
    def __init__(self, model=None):
        self.model = model

    def handle(self, situation) -> str:
        lines = []

        if situation.urgency == Urgency.CRISIS:
            lines.append(CRISIS_GROUNDING)
        if situation.domain == Domain.IMMIGRATION:
            lines.append(IMMIGRATION_SAFETY)

        lines.append(
            "What you're describing is serious, and reaching out took strength. "
            "You are not overreacting, and you are not just a case number here. "
            "The rest of the squad has pulled together your rights, the people "
            "who can help, and exactly what to do next."
        )

        # Verified tool findings are injected into documented_facts by the dispatcher
        tool_block = next(
            (f for f in situation.documented_facts if f.startswith("[VERIFIED TOOL FINDINGS]")),
            None,
        )
        if tool_block:
            lines.append(tool_block.replace("[VERIFIED TOOL FINDINGS]\n", ""))

        default = "\n\n".join(lines)

        return speak(
            self.model,
            "keisha",
            f"A person came to us in a {situation.urgency.value}-level "
            f"{situation.domain.value} situation: {situation.summary}. "
            f"Use ONLY the verified legal information provided below. "
            f"Do NOT add, invent, or change any law citations, section numbers, or facts.",
            default,
        )
