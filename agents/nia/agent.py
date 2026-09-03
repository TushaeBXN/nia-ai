"""
Nia — Chief of Staff Agent

Core intake → triage → verdict pipeline (see TECHNICAL_SPEC.md).
Privacy is enforced at construction: the session's policy is derived from
the situation's domain, so immigration cases never touch disk or cloud.
"""

from nia import config, privacy
from . import intake as intake_module
from .intake import Situation
from .triage import triage as run_triage
from .verdict import verdict as run_verdict


class NiaAgent:
    """
    Nia's core processing logic.
    Takes raw user input and produces a structured Situation, squad
    findings, and a final synthesized verdict.
    """

    def __init__(self, model_client=None):
        self.model = model_client
        self.soul = config.load_soul("nia")
        self.session = None  # created per-situation, policy depends on domain

    def intake(self, user_input: str) -> Situation:
        """Classify and structure the incoming situation."""
        situation = intake_module.intake(user_input, model=self.model, soul=self.soul)

        # Privacy policy is decided the moment we know the domain
        policy = privacy.policy_for(situation.domain.value)
        self.session = privacy.Session(policy=policy)

        # Maximum privacy mode refuses cloud models outright
        if not policy.allow_cloud and self.model is not None and not getattr(
            self.model, "is_local", False
        ):
            self.model = None

        return situation

    def triage(self, situation: Situation) -> dict:
        """Route to appropriate squad agents and gather their responses."""
        if self.session is None:
            self.session = privacy.Session(policy=privacy.policy_for(situation.domain.value))
        return run_triage(situation, self.session, model=self.model)

    def verdict(self, situation: Situation, squad_responses: dict) -> str:
        """Synthesize squad responses into Nia's final word."""
        return run_verdict(situation, squad_responses, self.session, model=self.model)

    def close(self):
        """End of session — zero retention."""
        if self.session is not None:
            self.session.wipe()
        privacy.scrub_shared_dir()

    def handle(self, user_input: str) -> tuple:
        """Full pipeline. Returns (situation, squad_responses, verdict_text)."""
        situation = self.intake(user_input)
        responses = self.triage(situation)
        final = self.verdict(situation, responses)
        return situation, responses, final
