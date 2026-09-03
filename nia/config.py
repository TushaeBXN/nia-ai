"""
Nia configuration — paths and model endpoints.

Everything is overridable by environment variable so a deployment
(community org, clinic, library) can relocate data without touching code.
"""

import os
from pathlib import Path

# Repo root (this file lives in nia/)
REPO_ROOT = Path(__file__).resolve().parent.parent

# Squad directory — where agents/ and coordination/ live.
# Defaults to this repo. If an external squad exists (e.g. ~/nia-squad),
# point NIA_SQUAD_DIR at it and Nia will use those SOUL.md files instead.
SQUAD_DIR = Path(os.environ.get("NIA_SQUAD_DIR", REPO_ROOT))

AGENTS_DIR = SQUAD_DIR / "agents"
COORDINATION_DIR = SQUAD_DIR / "coordination"

# In Lambda, /var/task is read-only — set NIA_SHARED_DIR=/tmp/nia-shared
# via the Lambda environment variable to redirect coordination writes to /tmp.
SHARED_DIR = Path(os.environ.get("NIA_SHARED_DIR", str(COORDINATION_DIR / "shared")))

KNOWLEDGE_DIR = REPO_ROOT / "knowledge"
RIGHTS_DIR = KNOWLEDGE_DIR / "rights"
RESOURCES_DIR = KNOWLEDGE_DIR / "resources"

# Model endpoints
OLLAMA_URL = os.environ.get("NIA_OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("NIA_MODEL", "nia-ft")

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = os.environ.get("NIA_CLAUDE_MODEL", "claude-sonnet-4-6")


def load_soul(agent_name: str) -> str:
    """Load an agent's SOUL.md persona file."""
    soul_path = AGENTS_DIR / agent_name / "SOUL.md"
    if soul_path.exists():
        return soul_path.read_text()
    return ""
