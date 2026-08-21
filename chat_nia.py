"""Nia — full companion runtime.

Memory, tools, voice, vision, document reading, voice input.

Run:  python3 chat_nia.py
      /look [q]      = webcam    /show path [q] = show image
      /listen        = speak     /converse      = voice conversation mode
      /file path [q] = send file contents
      /paste [q]     = multiline input (END to finish)
      /brief         = morning briefing   /evening = end-of-day recap
      /journal [q]   = journal session
      Ctrl-C to end.
"""
import argparse
import base64
import os
import random
import re
import threading
import time
import ollama

import nia_tools as tools
import voice
import vision
import hearing
from memory import Memory
from state import InternalState
from thoughts import ThoughtBuffer
from nia_persona import SYSTEM_PROMPT
import learnings as _learnings

_session_learnings: str = ""

MODEL        = os.environ.get("NIA_MODEL",        "nia")
HERMES_MODEL = os.environ.get("NIA_HERMES_MODEL", "amy-hermes")
VISION_MODEL = os.environ.get("NIA_VISION_MODEL", "gemma4:e2b")
CODE_MODEL   = os.environ.get("NIA_CODE_MODEL",   "deepseek-coder:6.7b")
MAX_TOOL_HOPS = 4
HISTORY_WINDOW = 16
CTX_WINDOW = 8192
KEEP_ALIVE = -1
MAX_LEARNINGS_CHARS = 2000
SELF_PORTRAIT = os.path.join(os.path.dirname(__file__), "nia.png")

# Signals that hermes should handle tool orchestration
_HERMES_RE = re.compile(
    r'\b(research|look up|find out|search|investigate|dig into'
    r'|eviction|credit report|credit dispute|debt collector|debt collection'
    r'|lawsuit|court|statute|fcra|fdcpa|fair housing|title vii|treaty'
    r'|legal|rights|law|policy|ordinance|regulation|ruling|case law'
    r'|compare|comprehensive|thorough|step by step|walk me through'
    r'|explain how|how do i fight|how do i dispute|what can i do about)\b',
    re.I,
)

_CODE_RE = re.compile(
    r'```|def |class |import |function |#!/|sql |query|script|code|debug|error\s+on\s+line',
    re.I,
)


def _needs_hermes(text: str) -> bool:
    """True when the request warrants multi-hop tool orchestration via hermes."""
    word_count = len(text.split())
    return word_count > 40 or bool(_HERMES_RE.search(text))


def _is_code_request(text: str) -> bool:
    return bool(_CODE_RE.search(text))

_TRAILER_RE = re.compile(
    r'(how\s+(else\s+)?can\s+i\s+(be\s+there|help|assist)'
    r'|i\'m\s+(all\s+ears|eager\s+to\s+assist|on\s+it|ready\s+to\s+(help|engage|support)|here\s+for\s+anything)'
    r'|just\s+say\s+the\s+word'
    r'|let\s+me\s+know\s+what\s+comes\s+up'
    r'|what\s+(else\s+is\s+on\s+your\s+mind|would\s+you\s+like\s+me\s+to\s+do)'
    r'|how\s+can\s+i\s+support)',
    re.I,
)


def _strip_trailers(text: str) -> str:
    lines = text.splitlines()
    while lines and _TRAILER_RE.search(lines[-1]):
        lines.pop()
    return "\n".join(lines).rstrip()


def _drop_images(msgs):
    result = []
    for m in msgs:
        if hasattr(m, "model_dump"):
            d = m.model_dump()
        else:
            d = dict(m)
        d.pop("images", None)
        result.append(d)
    return result


def build_context(mem, user_text, nia_state=None, absence=None,
                  pending_thoughts=None):
    system = SYSTEM_PROMPT + "\n\n" + mem.wake_up()
    if _session_learnings:
        system += "\n\n" + _session_learnings[:MAX_LEARNINGS_CHARS]
    if nia_state:
        system += "\n\n[Internal state]\n" + nia_state.state_summary()

    if pending_thoughts:
        thought_texts = [t for _, t in pending_thoughts]
        system += ("\n\n[Thoughts you had while they were away]\n- "
                   + "\n- ".join(thought_texts)
                   + "\n\nIf you share a thought, say it once, directly — "
                   "do NOT narrate that you had a thought, do NOT repeat the content twice. "
                   "Only assert things you are confident are true. "
                   "Never mention a specific URL, case name, or source you did not actually retrieve.")

    if absence:
        system += (f"\n\n[Time awareness] The person was away for {absence}. "
                   "If they ask how long, give your honest estimate.")

    hits = mem.search(user_text, k=4)
    if hits:
        system += ("\n\n[What this person has told you before]\n- "
                   + "\n- ".join(hits))
        conflicts = mem.check_contradiction(user_text)
        relevant_conflicts = [c for c in conflicts if c[0] not in hits]
        if relevant_conflicts:
            system += ("\n\n[Possible tension with something said before — be honest]\n- "
                       + "\n- ".join(t for t, _ in relevant_conflicts))
    return [{"role": "system", "content": system}]


def _b64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def run_turn(history, mem, image=None, nia_state=None,
             absence=None, pending_thoughts=None):
    user_msg = history[-1]
    if image:
        b64 = _b64_image(image)
        user_msg["images"] = [b64]
        print(f"  [vision] image attached ({len(b64)//1024}KB b64)")

    messages = build_context(mem, user_msg["content"], nia_state,
                             absence=absence,
                             pending_thoughts=pending_thoughts) + _drop_images(history)
    user_task = user_msg.get("content", "")

    # ── Vision: gemma4:e2b reads the doc, nia interprets ─────────────────────
    if image:
        vision_messages = [
            {"role": "system", "content":
                "You are a document and image reader. Examine this carefully. "
                "Transcribe ALL text, numbers, dates, names, and key details you see. "
                "If it's a document (debt letter, eviction notice, credit report, legal filing), "
                "extract every relevant field. Be thorough and literal."},
            {"role": "user", "content": user_task, "images": [b64]},
        ]
        vision_resp = ollama.chat(model=VISION_MODEL, messages=vision_messages,
                                  keep_alive=KEEP_ALIVE)
        description = vision_resp["message"].get("content", "").strip()
        print(f"  [vision] read: {description[:120]}...")

        if description:
            sys_msgs = build_context(
                mem, user_task, nia_state,
                absence=absence, pending_thoughts=pending_thoughts
            )
            sys_msgs[0]["content"] += (
                f"\n\n[Document/image contents — you just examined this]\n{description}"
                "\n\nTell the person exactly what this means, what their rights are, "
                "and what their options are. Give receipts."
            )
            clean_user = user_msg.copy()
            clean_user.pop("images", None)
            nia_messages = sys_msgs + _drop_images(history[:-1]) + [clean_user]
            resp = ollama.chat(model=MODEL, messages=nia_messages,
                               tools=tools.TOOLS, keep_alive=KEEP_ALIVE,
                               options={"num_ctx": CTX_WINDOW})
            msg = resp["message"]
            if msg.get("thinking"):
                with open("nia_thoughts.log", "a") as f:
                    f.write(msg["thinking"].strip() + "\n---\n")
            history.append(msg)
            if msg.get("content"):
                clean = _strip_trailers(msg["content"])
                msg["content"] = clean
                voice.speak_streamed(clean)
                mem.add("assistant", clean)
        if nia_state:
            nia_state.after_turn()
        return history

    # ── Routing: hermes works complex tool chains, nia speaks ─────────────────
    use_hermes = _needs_hermes(user_task)
    work_model = HERMES_MODEL if use_hermes else MODEL
    if use_hermes:
        print(f"  [router] complex request → hermes orchestrates")

    _seen_calls = {}
    msg = None

    for _ in range(MAX_TOOL_HOPS):
        resp = ollama.chat(model=work_model, messages=messages, tools=tools.TOOLS,
                           keep_alive=KEEP_ALIVE, options={"num_ctx": CTX_WINDOW})
        msg = resp["message"]
        if msg.get("thinking"):
            with open("nia_thoughts.log", "a") as f:
                f.write(msg["thinking"].strip() + "\n---\n")
        messages.append(msg)
        history.append(msg)

        calls = msg.get("tool_calls") or []
        if not calls:
            break

        for call in calls:
            fn = call["function"]
            name = fn["name"]
            args = fn.get("arguments", {})
            call_key = (name, tuple(sorted(
                (k, str(v)) for k, v in args.items()
            ) if isinstance(args, dict) else ()))
            if call_key in _seen_calls:
                result = _seen_calls[call_key]
                print(f"  [tools] dedup — skipping repeated {name}")
            else:
                result = tools.dispatch(name, args, mem)
                _seen_calls[call_key] = result
            reminder = (f"\n\n[You are mid-task. Complete the user's request: "
                        f"\"{user_task[:150]}\". Do not greet — keep working.]")
            messages.append({"role": "tool",
                              "content": (str(result) if result else "done") + reminder})
            history.append(messages[-1])

    # ── Nia voices the final answer (always) ─────────────────────────────────
    if use_hermes and msg and msg.get("content"):
        raw = msg["content"]
        voice_msgs = build_context(mem, user_task, nia_state) + [
            {"role": "assistant", "content": f"[Research]\n{raw}"},
            {"role": "user", "content": "Give me your read on this."},
        ]
        nia_resp = ollama.chat(model=MODEL, messages=voice_msgs,
                               keep_alive=KEEP_ALIVE, options={"num_ctx": CTX_WINDOW})
        final_msg = nia_resp["message"]
        history.append(final_msg)
        msg = final_msg

    if msg and msg.get("content"):
        clean = _strip_trailers(msg["content"])
        msg["content"] = clean
        voice.speak_streamed(clean)
        mem.add("assistant", clean)
    if nia_state:
        nia_state.after_turn()
    return history


def run_turn_streaming(history, mem, image=None, nia_state=None,
                       absence=None, pending_thoughts=None):
    """Generator variant of run_turn. Yields event dicts for SSE encoding.

    Events:
      {"type": "tool",  "name": str}
      {"type": "chunk", "text": str}
      {"type": "done",  "mood": str, "energy": float, "turn": int}
    """
    import logger as _log

    def _done():
        return {
            "type": "done",
            "mood":   nia_state.mood if nia_state else "focused",
            "energy": round(nia_state.energy, 2) if nia_state else 1.0,
            "turn":   nia_state.turn_count if nia_state else 0,
        }

    def _fake_stream(text):
        words = text.split()
        for i, word in enumerate(words):
            yield {"type": "chunk", "text": word + (" " if i < len(words) - 1 else "")}

    user_msg = history[-1]
    if image:
        b64 = _b64_image(image)
        user_msg["images"] = [b64]

    messages = build_context(mem, user_msg["content"], nia_state,
                             absence=absence,
                             pending_thoughts=pending_thoughts) + _drop_images(history)
    user_task = user_msg.get("content", "")

    # ── Document / vision case (sync describe, fake-stream reply) ─────────────
    if image:
        vision_messages = [
            {"role": "system", "content":
                "You are a document and image reader. Examine this carefully. "
                "Transcribe ALL text, numbers, dates, names, and key details you see. "
                "If it's a document (debt letter, eviction notice, credit report, legal filing), "
                "extract every relevant field. Be thorough and literal."},
            {"role": "user", "content": user_msg["content"], "images": [b64]},
        ]
        vision_resp = ollama.chat(model=VISION_MODEL, messages=vision_messages, keep_alive=KEEP_ALIVE)
        description = vision_resp["message"].get("content", "").strip()

        if description:
            sys_msgs = build_context(mem, user_msg["content"], nia_state,
                                     absence=absence, pending_thoughts=pending_thoughts)
            sys_msgs[0]["content"] += (
                f"\n\n[Document/image contents — you just examined this]\n{description}"
                "\n\nTell the person exactly what this means, what their rights are, "
                "and what their options are. Give receipts."
            )
            clean_user = user_msg.copy()
            clean_user.pop("images", None)
            nia_messages = sys_msgs + _drop_images(history[:-1]) + [clean_user]
            resp = ollama.chat(model=MODEL, messages=nia_messages, tools=tools.TOOLS,
                               keep_alive=KEEP_ALIVE, options={"num_ctx": CTX_WINDOW})
            msg = resp["message"]
            if msg.get("thinking"):
                with open("nia_thoughts.log", "a") as f:
                    f.write(msg["thinking"].strip() + "\n---\n")
            history.append(msg)
            if msg.get("content"):
                clean = _strip_trailers(msg["content"])
                msg["content"] = clean
                history[-1] = msg
                yield from _fake_stream(clean)
                voice.speak_streamed(clean)
                mem.add("assistant", clean)

        if nia_state:
            nia_state.after_turn()
        yield _done()
        return

    # ── Code path: deepseek-coder with true token streaming ──────────────────
    if _is_code_request(user_task):
        yield {"type": "tool", "name": "__code__"}
        full_text = ""
        stream = ollama.chat(model=CODE_MODEL, messages=messages,
                             stream=True, keep_alive=KEEP_ALIVE,
                             options={"num_ctx": CTX_WINDOW})
        for chunk in stream:
            token = chunk["message"].get("content", "")
            if token:
                full_text += token
                yield {"type": "chunk", "text": token}
        if full_text:
            clean = _strip_trailers(full_text)
            mem.add("assistant", clean)
            history.append({"role": "assistant", "content": clean})
            voice.speak_streamed(clean)
        if nia_state:
            nia_state.after_turn()
        yield _done()
        return

    # ── Routing: hermes works complex tool chains, nia speaks ─────────────────
    use_hermes = _needs_hermes(user_task)
    work_model = HERMES_MODEL if use_hermes else MODEL
    _seen_calls = {}
    msg = None

    for _ in range(MAX_TOOL_HOPS):
        with _log.Timer("model_call", model=work_model):
            resp = ollama.chat(model=work_model, messages=messages, tools=tools.TOOLS,
                               keep_alive=KEEP_ALIVE, options={"num_ctx": CTX_WINDOW})
        msg = resp["message"]
        if msg.get("thinking"):
            with open("nia_thoughts.log", "a") as f:
                f.write(msg["thinking"].strip() + "\n---\n")
        messages.append(msg)
        history.append(msg)

        calls = msg.get("tool_calls") or []
        if not calls:
            break

        for call in calls:
            fn   = call["function"]
            name = fn["name"]
            args = fn.get("arguments", {})
            yield {"type": "tool", "name": name}
            _log.log("tool_call", tool=name)

            call_key = (name, tuple(sorted(
                (k, str(v)) for k, v in args.items()
            ) if isinstance(args, dict) else ()))
            if call_key in _seen_calls:
                result = _seen_calls[call_key]
            else:
                result = tools.dispatch(name, args, mem)
                _seen_calls[call_key] = result

            reminder = (f"\n\n[You are mid-task. Complete the user's request: "
                        f"\"{user_task[:150]}\". Do not greet — keep working.]")
            messages.append({"role": "tool",
                              "content": (str(result) if result else "done") + reminder})
            history.append(messages[-1])

    # ── Nia voices the final answer (always) ─────────────────────────────────
    if use_hermes and msg and msg.get("content"):
        raw = msg["content"]
        voice_msgs = build_context(mem, user_task, nia_state) + [
            {"role": "assistant", "content": f"[Research]\n{raw}"},
            {"role": "user", "content": "Give me your read on this."},
        ]
        with _log.Timer("nia_voice", model=MODEL):
            nia_resp = ollama.chat(model=MODEL, messages=voice_msgs,
                                   keep_alive=KEEP_ALIVE, options={"num_ctx": CTX_WINDOW})
        msg = nia_resp["message"]
        history.append(msg)

    if msg and msg.get("content"):
        clean = _strip_trailers(msg["content"])
        msg["content"] = clean
        yield from _fake_stream(clean)
        voice.speak_streamed(clean)
        mem.add("assistant", clean)

    if nia_state:
        nia_state.after_turn()
    yield _done()


_CHECKIN_PROMPTS = {
    "focused":    "You've been quiet, staying focused. Check in with Brian about something specific — a task he mentioned, something he was working on. Direct and brief.",
    "fired_up":   "You've been quiet but the fire hasn't gone out. Say something sharp — a fact you've been sitting with, a pattern you noticed, or a question that's been nagging. Short.",
    "reflective": "You've been sitting with something. Share one thought that just surfaced — about the conversation, history, or the state of things. Keep it real.",
    "nurturing":  "You've been quiet and present. Check in with Brian — genuinely. Ask one question. Not about the work. About him.",
    "tired":      "You've been quiet. You're a little tired but still here. Say something short and honest.",
    "sharp":      "You've been alert and catching things. Share one sharp observation — a detail, a connection, something that doesn't add up or does. Crisp.",
}


def _spontaneous_thought(history, mem, nia_state):
    mood = nia_state.mood
    checkin_prompt = _CHECKIN_PROMPTS.get(mood, _CHECKIN_PROMPTS["focused"])

    system = (SYSTEM_PROMPT + "\n\n" + mem.wake_up() +
              "\n\n[Internal state]\n" + nia_state.state_summary() +
              f"\n\n[Instruction — do this NOW]\n{checkin_prompt}")

    messages = [{"role": "system", "content": system}] + _drop_images(history[-6:])

    try:
        resp = ollama.chat(model=MODEL, messages=messages, keep_alive=KEEP_ALIVE,
                           options={"num_ctx": CTX_WINDOW, "num_predict": 80})
        text = _strip_trailers(resp["message"].get("content", "").strip())
        if text and re.sub(r'[^\w]', '', text):
            voice.speak(text, emotion=mood)
            mem.add("assistant", text)
            history.append({"role": "assistant", "content": text})
            if len(history) > HISTORY_WINDOW:
                history[:] = history[-HISTORY_WINDOW:]
            nia_state.touch()
            nia_state.after_turn()
    except Exception:
        pass


def start_spontaneous_thread(history, mem, nia_state,
                              idle_threshold=120, check_interval=15):
    def _loop():
        while True:
            time.sleep(check_interval)
            if nia_state.busy:
                continue
            if nia_state.seconds_idle() >= idle_threshold:
                nia_state.busy = True
                try:
                    _spontaneous_thought(history, mem, nia_state)
                finally:
                    nia_state.busy = False

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t


def _warmup_models():
    """Pre-load models into Ollama memory at startup — eliminates first-reply cold lag."""
    def _ping(model):
        try:
            ollama.chat(model=model,
                        messages=[{"role": "user", "content": "hi"}],
                        keep_alive=KEEP_ALIVE,
                        options={"num_predict": 1, "num_ctx": 512})
            print(f"  [warmup] {model} ready")
        except Exception as e:
            print(f"  [warmup] {model} unavailable: {e}")

    for m in [MODEL, HERMES_MODEL, CODE_MODEL]:
        threading.Thread(target=_ping, args=(m,), daemon=True).start()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="image path for Nia to examine this turn")
    args = ap.parse_args()

    _warmup_models()
    mem = Memory()
    global _session_learnings
    _session_learnings = _learnings.load_recent_learnings()
    nia_state = InternalState()
    thought_buffer = ThoughtBuffer()

    history = [{"role": "assistant", "content": random.choice([
        "You're here. Good. What do you need?",
        "I was just sitting with some thoughts. What's going on?",
        "Back. What are we working on?",
        "Good. I have things to say. But first — what brings you in?",
        "You caught me mid-thought. What's on your mind?",
        "I'm here. Talk to me.",
        "The work doesn't stop. What are we tackling?",
        "Brian. What's the situation?",
    ])}]

    start_spontaneous_thread(history, mem, nia_state)
    thought_buffer.start(nia_state, history)

    print(
        "\n╔══════════════════════════════════════════════════════════╗\n"
        "║              N I A                                       ║\n"
        "║        The Minister of Verdicts                          ║\n"
        "╚══════════════════════════════════════════════════════════╝\n\n"
        "  /look [q]      = webcam     /show path [q] = show image\n"
        "  /listen        = speak      /converse      = voice mode\n"
        "  /file path [q] = send file  /paste [q]     = multiline\n"
        "  /brief         = briefing   /evening       = recap\n"
        "  /journal [q]   = journal    Ctrl-C to end\n"
    )

    try:
        while True:
            user = input("You: ").strip()
            if not user:
                continue

            image = args.image
            args.image = None

            # /converse — continuous voice conversation mode
            if user.startswith("/converse"):
                parts = user.split()
                silence_timeout = 0.8
                if len(parts) > 1:
                    try:
                        silence_timeout = float(parts[1])
                    except ValueError:
                        pass
                audio_dev = ":0"
                bh = hearing.find_blackhole()
                if bh:
                    audio_dev = f":{bh[0]}"
                    print(f"  [hearing] using BlackHole ({bh[1]})")
                else:
                    print("  [hearing] using mic")
                print(f"  Entering voice mode (pause={silence_timeout}s). Ctrl-C to stop.\n")
                try:
                    while True:
                        wav_path = hearing.listen_until_silence_vad(silence_timeout=silence_timeout)
                        heard = hearing.transcribe(wav_path)
                        try:
                            os.unlink(wav_path)
                        except OSError:
                            pass
                        if not heard:
                            continue
                        print(f"  [heard] {heard}")
                        mem.add("user", heard)
                        history.append({"role": "user", "content": heard})
                        nia_state.touch()
                        nia_state.busy = True
                        try:
                            history = run_turn(history, mem, nia_state=nia_state)
                        finally:
                            nia_state.busy = False
                        if len(history) > HISTORY_WINDOW:
                            history = history[-HISTORY_WINDOW:]
                except KeyboardInterrupt:
                    print("\n  (exited voice mode — back to typing)")
                continue

            # /file — send text file contents
            if user.startswith("/file"):
                parts = user[len("/file"):].strip().split(None, 1)
                if not parts:
                    print("  Usage: /file /path/to/file.txt [optional question]")
                    continue
                fpath = os.path.expanduser(parts[0])
                if not os.path.exists(fpath):
                    print(f"  (file not found: {fpath})")
                    continue
                try:
                    with open(fpath, "r", errors="replace") as f:
                        content = f.read()
                    q = parts[1] if len(parts) > 1 else "Here is the content:"
                    user = f"{q}\n\n{content}"
                    print(f"  [file] loaded {len(content)} chars from {fpath}")
                except Exception as e:
                    print(f"  (could not read file: {e})")
                    continue

            # Slash command expansions
            if user.lower() in ("/brief", "/briefing", "/morning", "/startday"):
                from datetime import datetime as _dt
                day = _dt.now().strftime("%A, %B %d, %Y")
                user = (f"Give me my morning briefing for {day}. "
                        "Use web_search to find relevant news — focus on policy, "
                        "community justice, wealth-building, and AI. "
                        "Pull my active goals from memory. Keep it sharp.")
            elif user.lower() in ("/evening", "/eod", "/recap"):
                user = ("Give me an end-of-day recap. "
                        "Reflect on what we worked on today, what's carried over, "
                        "and what's next. Brief and direct.")
            elif user.startswith("/journal"):
                q = user[len("/journal"):].strip()
                if not q:
                    user = ("Start a journal session with me. Ask me one question — "
                            "rotate through: highlight, challenge, learning, gratitude. "
                            "After I answer, save it with journal_entry and reflect back one observation.")
                else:
                    user = f"Save this journal entry and reflect on it: {q}"

            # /paste — multiline input
            if user.startswith("/paste"):
                q = user[len("/paste"):].strip() or "Here is what I'm sharing:"
                print("  Paste your content below. Type END on its own line when done.")
                lines = []
                while True:
                    try:
                        line = input()
                    except EOFError:
                        break
                    if line.strip() == "END":
                        break
                    lines.append(line)
                if not lines:
                    print("  (nothing pasted)")
                    continue
                content = "\n".join(lines)
                user = f"{q}\n\n{content}"
                print(f"  [paste] received {len(content)} chars")

            # /listen — push-to-talk
            if user.startswith("/listen"):
                parts = user.split()
                max_dur = 60.0
                if len(parts) > 1:
                    try:
                        max_dur = float(parts[1])
                    except ValueError:
                        pass
                wav_path = hearing.listen_until_silence_vad(max_duration=max_dur)
                heard = hearing.transcribe(wav_path)
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
                if not heard:
                    print("  (didn't catch anything)")
                    continue
                print(f"  [heard] {heard}")
                user = heard

            # /show — show an image or document
            elif user.startswith("/show"):
                parts = user[len("/show"):].strip().split(None, 1)
                if not parts:
                    print("  Usage: /show /path/to/image.jpg [optional question]")
                    continue
                img_path = os.path.expanduser(parts[0])
                if not os.path.exists(img_path):
                    print(f"  (file not found: {img_path})")
                    continue
                image = img_path
                q = parts[1] if len(parts) > 1 else \
                    "Read this document and tell me what it means and what my rights are."
                user = (
                    "There is an image or document attached. Examine it carefully. "
                    "Do not say you cannot see. Read what is there. "
                    "Then answer: " + q
                )

            # /look — webcam capture
            elif user.startswith("/look"):
                q = user[len("/look"):].strip() or \
                    "Look at me. Tell me exactly what you see."
                print("  [vision] capturing frame...")
                image = vision.capture()
                if not image:
                    print("  (couldn't capture — check camera permission)")
                    continue
                user = q

            # /self — Nia's own image
            elif user.startswith("/self"):
                if not os.path.exists(SELF_PORTRAIT):
                    print(f"  (no portrait at {SELF_PORTRAIT})")
                    continue
                q = user[len("/self"):].strip() or "What do you see?"
                image = SELF_PORTRAIT
                user = (
                    "You are looking at your own portrait. Look at it directly. "
                    "Describe what you see. Then answer: " + q
                )

            mem.add("user", user)
            history.append({"role": "user", "content": user})
            absence = nia_state.estimate_absence()
            pending_thoughts = thought_buffer.drain() if thought_buffer.has_thoughts() else []
            nia_state.touch()
            nia_state.busy = True
            print("  [Nia is thinking...]", flush=True)
            try:
                history = run_turn(history, mem, image=image, nia_state=nia_state,
                                   absence=absence, pending_thoughts=pending_thoughts)
            finally:
                nia_state.busy = False
            if len(history) > HISTORY_WINDOW:
                history = history[-HISTORY_WINDOW:]

    except (KeyboardInterrupt, EOFError):
        print("\nNia: The work continues. Until next time.")
        _learnings.run_session_end(history, mem, nia_state)


if __name__ == "__main__":
    main()
