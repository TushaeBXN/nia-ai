"""
Nia — Verdict (synthesis)

Turns squad findings into one clear, warm, actionable response.
With a model: Nia speaks in her own voice, guided by SOUL.md.
Without a model: a deterministic assembly of the squad's findings —
less poetry, same substance. People get helped either way.
"""

from nia import config
from .intake import Situation, Urgency

VERDICT_PROMPT = """Someone came to you with this situation:
{summary}

Urgency: {urgency}
Domain: {domain}

Your squad has gathered this information:
{squad_findings}

Now synthesize everything into a single response to this person.

STRICT RULES — failure to follow these makes Nia dangerous:
- Copy ALL law citations EXACTLY (e.g. "15 U.S.C. § 1681i") — never paraphrase
- Copy ALL website URLs, phone numbers, mailing addresses EXACTLY
- Copy ALL numbered steps EXACTLY — do not skip, merge, or reorder
- Do NOT fill in [brackets] — if a value is unknown, say so explicitly
- Do NOT invent laws, programs, or section numbers not in the squad findings
- If findings say something is automatic or free, say so explicitly
- If findings include a WARNING, include it word for word

Your response structure:
1. One warm sentence acknowledging what they're going through
2. THE MOST IMPORTANT FACT FIRST — if there's automatic relief, say it immediately
3. Their legal rights (cite exactly as written above)
4. Clear numbered next steps (copy from findings)
5. Where to go / who to call (exact URLs and phone numbers)
6. What to document or keep

You are not a lawyer — say so if legal action comes up."""

CRISIS_BANNER = (
    "If you or someone with you is in immediate danger, call 911 "
    "(or your local emergency number) first. Everything below can wait "
    "until you are safe."
)


def _format_findings(responses: dict) -> str:
    return "\n\n".join(f"[{name.upper()}]\n{text}" for name, text in responses.items())


def _assemble_offline(situation: Situation, responses: dict) -> str:
    """Deterministic synthesis when no model is available."""
    parts = []
    if situation.urgency == Urgency.CRISIS:
        parts.append(f"⚠  {CRISIS_BANNER}\n")
    parts.append(
        "I hear you, and I'm glad you reached out. What you're describing "
        "is real, and there are people and laws on your side. Here is what "
        "my squad put together for you:\n"
    )
    for name, text in responses.items():
        parts.append(f"── {name.upper()} " + "─" * max(0, 40 - len(name)) + f"\n{text}\n")
    parts.append(
        "One important thing: I'm not a lawyer, and this isn't legal advice. "
        "It's information and a map. The organizations above can connect you "
        "with people who can act on your behalf — most of them for free."
    )
    return "\n".join(parts)


def verdict(situation: Situation, squad_responses: dict, session, model=None) -> str:
    """Nia's final word to the person."""
    if model is not None:
        try:
            soul = config.load_soul("nia")
            text = model.complete(
                VERDICT_PROMPT.format(
                    summary=situation.summary,
                    urgency=situation.urgency.value,
                    domain=situation.domain.value,
                    squad_findings=_format_findings(squad_responses),
                ),
                system=soul or None,
            )
            if situation.urgency == Urgency.CRISIS and "911" not in text:
                text = f"⚠  {CRISIS_BANNER}\n\n{text}"
        except Exception:
            text = _assemble_offline(situation, squad_responses)
    else:
        text = _assemble_offline(situation, squad_responses)

    session.write(config.SHARED_DIR / "verdict.md", text)
    return text
