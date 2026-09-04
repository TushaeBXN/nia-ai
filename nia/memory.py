"""
Nia memory layer — backed by Engram (https://github.com/TushaeBXN/engram).

Keeps Nia's knowledge of a user's situation across sessions so she never
starts from zero. Session data is stored per-user under ~/.engram/nia/.

Usage:
    mem = NiaMemory()                 # or NiaMemory(user_id="phone_or_hash")
    mem.save_session(situation, verdict_text)
    prior = mem.recall(query_text, n=5)   # returns list of content strings
    warm_up = mem.warm_up()               # 170-token cold-start block
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

NIA_ENGRAM_ROOT = Path.home() / ".engram" / "nia"
NIA_COLLECTION = "nia_sessions"


def _load_engram(user_id: str):
    """Return (chateau, backend, searcher) — all lazy so Nia still runs without engram."""
    from engram.chateau import Chateau
    from engram.backends.chromadb_backend import ChromaDBBackend
    from engram.searcher import Searcher

    root = NIA_ENGRAM_ROOT / user_id
    root.mkdir(parents=True, exist_ok=True)

    chateau = Chateau(root)
    chateau.ensure_wing("nia")
    chateau.ensure_room("nia", "sessions")

    backend = ChromaDBBackend(
        collection_name=f"{NIA_COLLECTION}_{user_id}",
        persist_directory=str(root / "vectors"),
    )
    searcher = Searcher(backend, chateau)
    return chateau, backend, searcher


class NiaMemory:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self._chateau = None
        self._backend = None
        self._searcher = None

    def _init(self):
        if self._chateau is None:
            try:
                self._chateau, self._backend, self._searcher = _load_engram(self.user_id)
            except ImportError:
                pass  # engram not installed — memory silently disabled

    def available(self) -> bool:
        self._init()
        return self._chateau is not None

    def recall(self, query: str, n: int = 5) -> list[str]:
        """Semantic search over prior sessions. Returns content strings."""
        self._init()
        if not self._searcher:
            return []
        try:
            # No wing/room filter — collection is already user-scoped
            hits = self._searcher.search(query, n=n)
            return [h.get("text", h.get("content", "")) for h in hits if h]
        except Exception:
            return []

    def save_session(self, situation, verdict: str) -> None:
        """Persist the situation summary + verdict after each session."""
        self._init()
        if not self._chateau:
            return
        try:
            from engram.chateau import Drawer

            ts = datetime.now(timezone.utc).isoformat()
            domain = situation.domain.value
            state = situation.state or "unknown"

            content = (
                f"[{ts}] domain={domain} state={state}\n"
                f"SITUATION: {situation.summary}\n"
                f"VERDICT: {verdict[:800]}"
            )

            drawer = Drawer(
                content=content,
                wing="nia",
                room="sessions",
                hall=f"{domain}-{ts[:10]}",
                tags=[domain, state],
            )
            self._chateau.save_drawer(drawer)
            self._backend.add(
                drawer.id,
                drawer.content,
                {"wing": drawer.wing, "room": drawer.room, "hall": drawer.hall,
                 "domain": domain, "state": state},
            )
        except Exception:
            pass  # memory failure must never crash Nia

    def warm_up(self) -> str:
        """Return a compact context block (~170 tokens) for cold-start injection."""
        self._init()
        if not self._searcher:
            return ""
        try:
            hits = self._searcher.search("situation domain urgency verdict", n=3)
            if not hits:
                return ""
            lines = ["[PRIOR SESSIONS — what this person has been working on]"]
            for h in hits:
                text = h.get("text", h.get("content", ""))
                lines.append(f"• {text[:200]}")
            return "\n".join(lines)
        except Exception:
            return ""
