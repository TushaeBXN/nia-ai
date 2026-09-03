"""
Privacy enforcement — the TECHNICAL_SPEC privacy spec, in code.

Rules implemented here:
  1. ZERO retention by default — any coordination file written during a
     session is deleted when the session ends.
  2. Immigration = MAXIMUM PRIVACY MODE — nothing is ever written to disk,
     no logs, no session storage, and cloud models are refused.
  3. No user-identifying information in anything Nia persists.

This module is not optional. This is foundational.
"""

from dataclasses import dataclass, field
from pathlib import Path

from . import config

# Domains that get maximum privacy mode. Add here as needed —
# e.g. domestic-violence support would belong here too.
MAX_PRIVACY_DOMAINS = {"immigration"}


@dataclass
class PrivacyPolicy:
    """What a session is allowed to do with a person's information."""
    allow_disk: bool = True     # may coordination files be written at all?
    allow_cloud: bool = True    # may the situation be sent to a cloud model?
    retain: bool = False        # zero retention by default — never True today

    @property
    def max_privacy(self) -> bool:
        return not self.allow_disk


def policy_for(domain: str) -> PrivacyPolicy:
    """Privacy policy for a situation domain."""
    if domain in MAX_PRIVACY_DOMAINS:
        return PrivacyPolicy(allow_disk=False, allow_cloud=False, retain=False)
    return PrivacyPolicy(allow_disk=True, allow_cloud=True, retain=False)


@dataclass
class Session:
    """
    Tracks every file a session touches so it can be wiped afterward.
    Use as a context manager so wiping happens even on crash or Ctrl+C.
    """
    policy: PrivacyPolicy = field(default_factory=PrivacyPolicy)
    written: list = field(default_factory=list)

    def write(self, path: Path, content: str) -> bool:
        """Write a coordination file — only if the policy allows disk."""
        if not self.policy.allow_disk:
            return False
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        if path not in self.written:
            self.written.append(path)
        return True

    def wipe(self):
        """Delete everything this session wrote. Zero retention."""
        for path in self.written:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass
        self.written.clear()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.wipe()
        return False


def scrub_shared_dir():
    """
    Safety net: remove any leftover case files from coordination/shared/.
    Runs at CLI startup and shutdown so a crashed session never leaves
    someone's situation on disk.
    """
    shared = config.SHARED_DIR
    if not shared.exists():
        return
    for f in shared.iterdir():
        if f.is_file() and f.name != ".gitkeep":
            try:
                f.unlink()
            except OSError:
                pass
