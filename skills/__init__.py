"""
Nia Skills Registry

Maps 25 Claude Code skills to Nia's squad agents and domain contexts.
Each skill is a structured workflow that a squad agent can invoke or
reference when assembling a response for a user situation.
"""

from .registry import SKILL_MAP, skills_for_domain, skill_prompt

__all__ = ["SKILL_MAP", "skills_for_domain", "skill_prompt"]
