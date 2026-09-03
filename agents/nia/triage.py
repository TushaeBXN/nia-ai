"""
Nia — Triage (squad routing)

Routes a structured Situation to the assigned squad agents, gathers their
findings, and (privacy permitting) writes the file-based coordination
state described in TECHNICAL_SPEC.md:

    coordination/shared/current_case.md   — written by Nia on intake
    coordination/shared/<agent>_notes.md  — each agent's findings
    coordination/shared/verdict.md        — Nia's final synthesis

In maximum privacy mode (immigration), nothing touches disk —
coordination happens in memory only.
"""

import importlib

from nia import config
from .intake import Situation


def _case_file_content(situation: Situation) -> str:
    facts = "\n".join(f"- {f}" for f in situation.documented_facts)
    return f"""# Current Case
**Domain:** {situation.domain.value}
**Urgency:** {situation.urgency.value}
**State:** {situation.state or "unknown"}
**Assigned:** {", ".join(situation.squad_assignment)}

## Summary
{situation.summary}

## Documented Facts
{facts}
"""


def load_agent(name: str, model=None):
    """Dynamic agent loading by name (agents/<name>/agent.py)."""
    module = importlib.import_module(f"agents.{name}.agent")
    return module.Agent(model)


def triage(situation: Situation, session, model=None) -> dict:
    """
    Run the situation past each assigned squad agent.
    Returns {agent_name: findings}. Writes coordination files only when
    the session's privacy policy allows disk.
    """
    session.write(config.SHARED_DIR / "current_case.md", _case_file_content(situation))

    # Run tools FIRST — verified findings go into agent context before model speaks
    from tools.dispatcher import dispatch, format_findings
    tool_findings = dispatch(situation)
    verified_block = format_findings(tool_findings)
    if verified_block:
        situation.documented_facts.insert(0, f"[VERIFIED TOOL FINDINGS]\n{verified_block}")

    responses = {}
    for name in situation.squad_assignment:
        try:
            agent = load_agent(name, model)
            findings = agent.handle(situation)
        except Exception as e:
            findings = f"[{name} unavailable: {e}]"
        responses[name] = findings
        session.write(config.SHARED_DIR / f"{name}_notes.md", findings)

    # Resource Router — every verdict ends with real people to call
    from tools.resource_router import format_matches
    responses["resources"] = (
        "WHO CAN HELP (national — free or low-cost):\n\n"
        + format_matches(situation.domain.value)
    )

    return responses
