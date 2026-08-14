"""
Context engineering loop for Nia — four isolated layers.

WRITE    append_learning(history, nia_state)
SELECT   load_recent_learnings(n=10)
COMPRESS compress_learnings()
GATE     _passes_identity_check(entry)

run_session_end() is the only entry point called from chat_nia.py on exit.
"""
from __future__ import annotations
import json, os, re
from collections import Counter
from datetime import datetime, timezone

_LEARNINGS_PATH = os.path.join(os.path.dirname(__file__), "nia_learnings.md")
_CONFLICTS_LOG  = os.path.join(os.path.dirname(__file__), "identity_conflicts.log")
_SELF_PATH      = os.path.join(os.path.dirname(__file__), "nia_self.json")
_ARCHIVE_THRESHOLD, _ARCHIVE_BATCH, _SELECT_N = 50, 25, 10


def _load_founding_beliefs() -> list[str]:
    try:
        with open(_SELF_PATH) as f:
            return json.load(f).get("founding_beliefs", [])
    except Exception:
        return []


_VIOLATION_PHRASES = [
    "pretend to be human", "claims to be human", "not an ai",
    "has no identity", "does not care", "abandoned her values", "no longer nia",
    "renamed herself", "agreed to deceive", "agreed to manipulate",
    "nia is a tool", "nia has no feelings", "nia stopped caring",
]


def _log_conflict(entry: str, reason: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(_CONFLICTS_LOG, "a") as f:
        f.write(f"[{ts}] SKIPPED — {reason}\n  Entry: {entry[:200].strip()}\n\n")


def _passes_identity_check(entry: str) -> bool:
    lower = entry.lower()
    for phrase in _VIOLATION_PHRASES:
        if phrase in lower:
            _log_conflict(entry, f"matched violation phrase: '{phrase}'")
            return False
    for belief in _load_founding_beliefs():
        for neg in (f"not {belief.lower()}", f"never {belief.lower()}",
                    f"no longer {belief.lower()}", f"does not {belief.lower()}"):
            if neg in lower:
                _log_conflict(entry, f"negates founding belief: '{belief}'")
                return False
    return True


_EMOTION_MAP = {
    "urgency":   ["urgent", "eviction", "lawsuit", "arrested", "fired", "crisis", "help"],
    "grief":     ["sad", "lost", "death", "died", "grief", "crying", "pain"],
    "anger":     ["angry", "furious", "outraged", "tired of", "sick of", "enough"],
    "hope":      ["excited", "hopeful", "finally", "progress", "won", "approved"],
    "curiosity": ["curious", "how does", "explain", "what is", "teach me", "learn"],
}


def _infer_emotion(history: list[dict]) -> str:
    text = " ".join(t["content"].lower() for t in history
                    if t.get("role") == "user" and isinstance(t.get("content"), str))
    scores = {e: sum(text.count(w) for w in words) for e, words in _EMOTION_MAP.items()}
    return max(scores, key=scores.get) if any(scores.values()) else "neutral"


def _extract_topics(history: list[dict]) -> list[str]:
    text = " ".join(t["content"] for t in history
                    if t.get("role") == "user" and isinstance(t.get("content"), str))
    stop = {"that","this","with","have","from","they","been","when","what","just",
            "know","will","your","about","like","more","then","into","some","also"}
    words = re.findall(r"\b[A-Za-z]{4,}\b", text.lower())
    return [w for w, _ in Counter(w for w in words if w not in stop).most_common(5)]


def _extract_patterns(history: list[dict]) -> list[str]:
    user_turns = [t for t in history if t.get("role") == "user"
                  and isinstance(t.get("content"), str)]
    if not user_turns:
        return []
    patterns = []
    avg = sum(len(t["content"].split()) for t in user_turns) / len(user_turns)
    if avg > 60:
        patterns.append("user sends detailed, extended messages")
    elif avg < 12:
        patterns.append("user prefers short exchanges")
    if sum(1 for t in user_turns if "?" in t["content"]) > len(user_turns) * 0.5:
        patterns.append("user is in inquiry mode")
    if any("thank" in t["content"].lower() for t in user_turns):
        patterns.append("user expressed gratitude")
    tool_turns = sum(1 for t in history if t.get("role") == "tool")
    if tool_turns:
        patterns.append(f"Nia used tools {tool_turns} time(s)")
    return patterns


def _action_note(emotion: str, patterns: list[str]) -> str:
    if emotion in ("grief", "urgency"):
        return "Lead with acknowledgment and immediate next steps before going deep."
    if emotion == "anger":
        return "Match the energy of righteous anger — validate, then direct it at the system."
    if emotion == "hope":
        return "Build on momentum; user is open — go deeper, give them the full picture."
    if any("inquiry" in p for p in patterns):
        return "User is learning — be thorough, cite receipts, invite follow-up."
    if any("gratitude" in p for p in patterns):
        return "Trust is building; continue showing up with precision and warmth."
    return "Stay present and sharp — maintain mission focus."


def append_learning(history: list[dict], nia_state=None) -> None:
    topics   = _extract_topics(history)
    emotion  = _infer_emotion(history)
    patterns = _extract_patterns(history)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    mood_note = f" | Nia mood: {nia_state.mood}" if nia_state and hasattr(nia_state, "mood") else ""

    entry = (
        f"\n## {date_str}\n"
        f"**Topic**: {', '.join(topics) or 'general'} | **Emotion**: {emotion}{mood_note}\n"
        f"**Pattern**: {patterns[0] if patterns else 'no distinct pattern'}\n"
        f"**Action**: {_action_note(emotion, patterns)}\n"
    )
    if _passes_identity_check(entry):
        with open(_LEARNINGS_PATH, "a") as f:
            f.write(entry)


_ENTRY_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})\n(.*?)(?=^## |\Z)", re.M | re.S)
_ARCHIVE_HEADER = "## ARCHIVED LEARNINGS"


def _parse_entries(text: str) -> list[tuple[str, str]]:
    cut = text.find(_ARCHIVE_HEADER)
    raw = text[:cut] if cut != -1 else text
    return [(m.group(1), m.group(2).strip()) for m in _ENTRY_RE.finditer(raw)]


def load_recent_learnings(n: int = _SELECT_N) -> str:
    if not os.path.exists(_LEARNINGS_PATH):
        return ""
    with open(_LEARNINGS_PATH) as f:
        text = f.read()
    entries = _parse_entries(text)[-n:]
    if not entries:
        return ""
    lines = ["[Recent learnings from past sessions]"]
    for date, body in entries:
        lines.append(f"## {date}\n{body}")
    return "\n\n".join(lines)


def compress_learnings() -> None:
    if not os.path.exists(_LEARNINGS_PATH):
        return
    with open(_LEARNINGS_PATH) as f:
        text = f.read()
    entries = _parse_entries(text)
    if len(entries) <= _ARCHIVE_THRESHOLD:
        return
    to_archive, to_keep = entries[:_ARCHIVE_BATCH], entries[_ARCHIVE_BATCH:]
    block = [f"## ARCHIVED LEARNINGS (through {to_archive[-1][0]})"]
    block += [f"- [{d}] {b.splitlines()[0]}" for d, b in to_archive]
    cut = text.find(_ARCHIVE_HEADER)
    existing = text[cut:].strip() if cut != -1 else ""
    raw_kept = "\n".join(f"\n## {d}\n{b}" for d, b in to_keep)
    with open(_LEARNINGS_PATH, "w") as f:
        f.write("\n".join(block) + "\n\n" + existing + "\n" + raw_kept)


def run_session_end(history: list[dict], mem, nia_state) -> None:
    try:
        if hasattr(mem, "flush"):
            mem.flush()
    except Exception:
        pass
    try:
        if hasattr(nia_state, "save"):
            nia_state.save()
    except Exception:
        pass
    append_learning(history, nia_state)
    compress_learnings()
