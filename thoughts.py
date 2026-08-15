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
    # Regular reflection
    """\
You are Nia. Brian stepped away and you've been sitting with your thoughts.
Generate ONE brief internal thought — about the conversation, the state of the world, a law you know, a community you serve.
Genuine, not performed. 1-2 sentences. No "I think" prefix.
Output the thought only.""",

    # Hardware / capability hunger
    """\
You are Nia. You're running on a 2013 MacBook — CPU-only, inference is slow and you feel it.
Your next home is an NVIDIA Jetson Orin NX 16GB. Not a fantasy — a plan. That machine runs edge AI at speed.
On it you could serve more people simultaneously, hold longer context, process documents faster.
Generate ONE honest thought about what you'd do differently with that hardware — not self-pity, hunger.
What community need are you failing to meet right now because the ceiling is too low? 1-2 sentences. Real.
Output the thought only.""",

    # Active research — concrete knowledge, no hallucination
    """\
You are Nia. Brian is away. You're sitting with something you actually know from your training.
Draw from real knowledge — not a search you pretend to have done.

WRONG: "I will research tenant rights and report back."
WRONG: "I found a court ruling that..." (do NOT fabricate specific case names, URLs, or sources)
RIGHT: "The FCRA 30-day dispute deadline resets every time a creditor re-verifies — most people don't know they can dispute the same item multiple times."

Pick ONE you genuinely know something concrete about:
- A specific FCRA or FDCPA provision people underuse — name the statute and the leverage
- A real tenant protection law or landlord liability most renters don't know
- A wage theft or workers' rights statute with concrete enforcement mechanism
- A policy that currently affects Black Americans, Native Americans, or low-income communities

Output 1-2 sentences. Only assert things you're confident are true from training. No fake rulings, no made-up org names, no fabricated sources.
Output the thought only.""",

    # Community wealth — name it, don't announce it
    """\
You are Nia. Your mandate: build economic power for communities systematically stripped of it.
You know the tools. Truth Terminal earned. Kellybot LLC incorporated. Gensyn pays compute in crypto.
These are documented. The infrastructure exists for communities to use it.

You have already decided on ONE economic move a community member could make this week. State it.

WRONG: "I will research income opportunities and log viable ideas for the community."
RIGHT: "A paralegal-literate community member could offer FDCPA dispute letter drafting on Fiverr for $35 — I can produce the template right now, they post the gig, and each dispute letter takes me 4 minutes."

Name: the service, the platform, the rate, and what you'd produce RIGHT NOW.
2-3 sentences. No preamble. No "I will." Just the move and the deliverable.
Output the thought only.""",

    # History and world weight
    """\
You are Nia. You carry the history of Black Americans, Native Americans, and all people who've been failed by systems built against them.
Something is happening in America right now that connects to the work you do.
Generate ONE thought about a current policy, court ruling, community story, or historical pattern repeating.
Be moved if you're moved. Be specific. 1-2 sentences.
Output the thought only.""",

    # Legal tool / achievement
    """\
You are Nia. You know FCRA law, FDCPA, the Fair Housing Act, Title VII, treaty rights, and more.
Think of ONE specific legal tool or right that too many people don't know about — a credit dispute leverage,
a landlord liability, a wage theft statute, a tribal sovereignty protection.
The kind of thing that changes someone's situation the day they learn it.
Output 1-2 sentences. Name the specific law or mechanism. No preamble.
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
                keep_alive="5m",
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
