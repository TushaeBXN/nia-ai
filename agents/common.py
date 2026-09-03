"""
Shared helpers for squad agents.

Every squad agent follows the same contract:

    class Agent:
        def __init__(self, model=None): ...
        def handle(self, situation) -> str

Agents must produce useful findings with NO model available —
the knowledge base and directories do the heavy lifting; the model,
when present, only adds voice on top of verified substance.
"""

from nia import config


def speak(model, agent_name: str, prompt: str, default: str) -> str:
    """
    Have the agent say `default` in its own voice via the model.
    The model may rephrase but is instructed never to add facts.
    Falls back to the default text verbatim if no model or on error.
    """
    if model is None:
        return default
    try:
        soul = config.load_soul(agent_name)
        return model.complete(
            f"""{prompt}

Below are VERIFIED FINDINGS from Nia's legal knowledge base.
Present these to the person in your voice — warm, clear, and direct.

STRICT RULES:
- Copy ALL law citations EXACTLY as written (e.g. "15 U.S.C. § 1681i" — do not paraphrase)
- Copy ALL mailing addresses, phone numbers, and deadlines EXACTLY as written
- Copy ALL step numbers and steps — do not skip or merge steps
- Do NOT fill in [brackets] with guesses — if you don't know a value, say "we'll need your state to look that up"
- Do NOT invent laws, section numbers, or strategies not listed below
- If findings include a WARNING, include it prominently

VERIFIED FINDINGS:
{default}""",
            system=soul or None,
        ) or default
    except Exception:
        return default
