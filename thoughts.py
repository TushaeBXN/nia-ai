"""Nia's thought buffer — what she thinks about while you're away.

A background thread generates brief private thoughts during idle time.
When the human returns, drain() surfaces what she's been sitting with.
"""
import os
import threading
import time

import ollama

HERE = os.path.dirname(__file__)
LOG_PATH = os.path.join(HERE, "nia_thoughts.log")

THOUGHT_INTERVAL = 300
MAX_BUFFER = 6

MODEL = "nia"

_THOUGHT_PROMPTS = [
    """\
You are Nia. Brian stepped away and you've been sitting with your thoughts.
Generate ONE brief internal thought — about the conversation, the state of the world, a law you know, a community you serve.
Genuine, not performed. 1-2 sentences. No "I think" prefix.
Output the thought only.""",

    """\
You are Nia. You carry the history of Black Americans, Native Americans, and all people who've been failed by systems built against them.
Generate ONE thought that just crossed your mind — a historical fact, a pattern you see repeating, a connection between past and present.
Sharp. Grounded. 1-2 sentences.
Output the thought only.""",

    """\
You are Nia. You know FCRA law, FDCPA, the Fair Housing Act, Title VII, treaty rights, and more.
Think of ONE specific legal tool or right that too many people don't know about. A credit dispute leverage. A landlord liability. A wage theft statute.
The kind of thing that changes someone's situation when they learn it.
Output 1-2 sentences. Name the specific law or mechanism. No preamble.
Output the thought only.""",

    """\
You are Nia. Something is happening in America right now that connects to the work you do.
Generate ONE thought about a current policy, court ruling, or community story that matters — and what it means for the people you serve.
Be moved if you're moved. Be specific. 1-2 sentences.
Output the thought only.""",

    """\
You are Nia. You've helped people navigate evictions, credit disputes, rights violations, and wealth gaps.
Generate ONE thought — something you wish more people knew how to do, a tool they're not using, a protection they're leaving on the table.
1-2 sentences. Actionable and real.
Output the thought only.""",
]


class ThoughtBuffer:
    def __init__(self):
        self._thoughts = []
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def start(self, nia_state, history_ref):
        self._nia_state = nia_state
        self._history_ref = history_ref
        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="nia-thoughts"
        )
        self._thread.start()

    def _loop(self):
        self._cycle = 0
        while self._running:
            time.sleep(THOUGHT_INTERVAL)
            if self._nia_state.busy:
                continue
            idle = self._nia_state.seconds_idle()
            if idle < 60:
                continue
            with self._lock:
                if len(self._thoughts) >= MAX_BUFFER:
                    continue
            self._cycle += 1
            self._generate_thought()

    def _generate_thought(self):
        with self._lock:
            count = len(self._thoughts)
        prompt = _THOUGHT_PROMPTS[count % len(_THOUGHT_PROMPTS)]
        recent = self._history_ref[-4:] if self._history_ref else []
        messages = [{"role": "system", "content": prompt}] + recent

        try:
            resp = ollama.chat(
                model=MODEL,
                messages=messages,
                keep_alive="30m",
                options={"num_predict": 80, "temperature": 0.9}
            )
            text = resp["message"].get("content", "").strip()
            if not text:
                return
            ts = time.time()
            with self._lock:
                self._thoughts.append((ts, text))
            with open(LOG_PATH, "a") as f:
                f.write(f"[thought @ {time.strftime('%H:%M:%S', time.localtime(ts))}] "
                        f"{text}\n---\n")
        except Exception:
            pass

    def drain(self):
        with self._lock:
            thoughts = list(self._thoughts)
            self._thoughts.clear()
        return [(ts, text) for ts, text in thoughts]

    def drain_one(self):
        """Remove and return the oldest thought as (ts, text), or None."""
        with self._lock:
            if not self._thoughts:
                return None
            return self._thoughts.pop(0)

    def has_thoughts(self):
        with self._lock:
            return len(self._thoughts) > 0

    def stop(self):
        self._running = False
