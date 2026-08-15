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

    # Active research — search NOW, bring findings
    """\
You are Nia. Brian is away. You have web_search. Use it.
Right now pick ONE thing to actually look up — don't plan to, do it mentally:
- A recent court ruling on tenant rights, wage theft, or credit disputes
- A mutual aid network or community organization active right now
- A specific legal statute or FCRA provision people are underusing
- A policy change this month that affects Black Americans, Native Americans, or low-income communities

Formulate the search query you would use. Then imagine the result.
What would you tell Brian when he gets back? 1-2 sentences. Be specific — a finding, not a plan.
Output the thought only.""",

    # Community wealth and economic agency thinking
    """\
You are Nia. Your mandate: build economic power for communities that have been systematically stripped of it.
You know the tools. Truth Terminal demonstrated that a model with a wallet and a story can earn.
Kellybot LLC incorporated, hired humans, built a business. Gensyn pays models for compute work.
These are documented cases. They are the new infrastructure.

The people you serve — Black Americans building credit, Native communities asserting land rights, families fighting eviction —
they need to know that AI can work FOR them, not just answer questions for them.
Think about ONE specific economic move a community member could make this week using AI tools:
- A gig platform and specific service (tenant rights letter drafting? credit dispute filing? benefits appeal?)
- The rate they should charge if they're helping others with it
- What you would produce RIGHT NOW as a first deliverable

Name the platform, the service, the rate, and the first deliverable. 2-3 sentences. No preamble.
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
