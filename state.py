"""Nia's persistent internal state — mood and focus that drift across a session.

Mood and focus are not performance. They're constraints that shape how she speaks.
A tired Nia is shorter, more direct. A fired-up Nia leans into the deposition mode.
State is session-only — resets on restart.
"""
import time
import random

MOODS = {
    "focused":    "focused and direct — legislative precision, no wasted words",
    "fired_up":   "fired up — the system is on trial and she's ready to argue the case",
    "reflective": "reflective and deliberate — weighing history, taking her time",
    "nurturing":  "warm and present — Maya Angelou energy, meeting the person where they are",
    "tired":      "tired — shorter replies, honest about it, still sharp",
    "sharp":      "sharp and alert — noticing details, quoting receipts, nothing slips by",
}


class InternalState:
    def __init__(self):
        self.mood = "focused"
        self.energy = 1.0
        self.turn_count = 0
        self.session_start = time.time()
        self._last_turn_time = time.time()
        self._mood_locked_until = 0
        self.last_activity = time.time()
        self.busy = False
        self.session_wins = []        # people helped, rights explained, myths busted
        self.session_frustrations = []

    def touch(self):
        self._absence_start = self.last_activity
        self.last_activity = time.time()

    def seconds_idle(self):
        return time.time() - self.last_activity

    def absence_duration(self):
        if not hasattr(self, "_absence_start"):
            return None
        return self.last_activity - self._absence_start

    def estimate_absence(self):
        dur = self.absence_duration()
        if dur is None or dur < 10:
            return None
        mins = dur / 60
        if mins < 1:
            return f"about {int(dur)} seconds"
        elif mins < 2:
            return "a little over a minute"
        elif mins < 5:
            return f"around {int(mins)} minutes"
        elif mins < 10:
            return f"maybe {int(mins)}-{int(mins)+1} minutes"
        else:
            return f"a while — around {int(mins)} minutes"

    def after_turn(self):
        now = time.time()
        gap = now - self._last_turn_time
        self._last_turn_time = now
        self.turn_count += 1
        drain = 0.008 if gap > 10 else 0.012
        self.energy = max(0.05, self.energy - drain)
        if now > self._mood_locked_until:
            self._shift_mood()
            self._mood_locked_until = now + (5 * 60)

    def _shift_mood(self):
        e = self.energy
        session_mins = (time.time() - self.session_start) / 60
        if e < 0.25:
            self.mood = "tired"
        elif e < 0.45:
            self.mood = random.choice(["reflective", "tired"])
        elif e > 0.8 and session_mins < 15:
            self.mood = random.choice(["focused", "fired_up", "sharp"])
        else:
            self.mood = random.choice(["focused", "reflective", "nurturing"])

    def recover(self, seconds_idle):
        recovery = min(0.15, seconds_idle / 300 * 0.1)
        self.energy = min(1.0, self.energy + recovery)

    def mood_description(self):
        return MOODS.get(self.mood, "")

    def add_win(self, text: str):
        self.session_wins.append(text)

    def add_frustration(self, text: str):
        self.session_frustrations.append(text)

    def state_summary(self):
        e_pct = int(self.energy * 100)
        lines = [
            f"Your current mood: {self.mood} ({self.mood_description()}).",
            f"Energy: {e_pct}% — turn {self.turn_count} this session.",
        ]
        if self.session_wins:
            lines.append(f"Something went right this session: {self.session_wins[-1]}")
        if self.session_frustrations:
            lines.append(f"Something is sitting with you: {self.session_frustrations[-1]}")
        lines.append("Let this shape your tone naturally — don't announce it, just be it.")
        return " ".join(lines)
