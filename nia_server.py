"""Nia — web interface at http://localhost:3100

Run:  python3 nia_server.py
"""
import asyncio
import base64
import json
import os
import queue
import random
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import chat_nia as nia
from chat_nia import run_turn, run_turn_streaming, start_spontaneous_thread, HISTORY_WINDOW
from memory import Memory
from state import InternalState
from thoughts import ThoughtBuffer
import learnings as _learnings
import vision

_mem       = Memory()
_nia_state = InternalState.restore()
_thought_buffer = ThoughtBuffer()
_lock      = asyncio.Lock()
_executor  = ThreadPoolExecutor(max_workers=1)

_OPENERS = [
    "You're here. Good. What do you need?",
    "I was just sitting with some thoughts. What's going on?",
    "Back. What are we working on?",
    "I'm here. Talk to me.",
    "The work doesn't stop. What are we tackling?",
    "Brian. What's the situation?",
    "Good. I have things to say. But first — what brings you in?",
    "You caught me mid-thought. What's on your mind?",
]
_PRIMER = {"role": "assistant", "content": random.choice(_OPENERS)}
_history = [_PRIMER]

nia._session_learnings = _learnings.load_recent_learnings()
start_spontaneous_thread(_history, _mem, _nia_state)
_thought_buffer.start(_nia_state, _history)

app = FastAPI(title="Nia")
app.mount("/static", StaticFiles(directory=HERE), name="static")


class ChatRequest(BaseModel):
    message: str
    image_b64: str | None = None


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=_UI_HTML)


@app.post("/chat")
async def chat(req: ChatRequest):
    async with _lock:
        image_path = None
        if req.image_b64:
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            tmp.write(base64.b64decode(req.image_b64))
            tmp.close()
            image_path = tmp.name

        absence = _nia_state.estimate_absence()
        pending_thoughts = _thought_buffer.drain() if _thought_buffer.has_thoughts() else []
        _nia_state.touch()
        _mem.add("user", req.message)
        _history.append({"role": "user", "content": req.message})

        _nia_state.busy = True
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _executor,
                lambda: run_turn(
                    _history, _mem,
                    image=image_path,
                    nia_state=_nia_state,
                    absence=absence,
                    pending_thoughts=pending_thoughts,
                ),
            )
            _history[:] = result
        finally:
            _nia_state.busy = False
            if image_path:
                try:
                    os.unlink(image_path)
                except OSError:
                    pass

        if len(_history) > HISTORY_WINDOW:
            _history[:] = _history[-HISTORY_WINDOW:]

        reply = ""
        for msg in reversed(_history):
            if msg.get("role") == "assistant" and msg.get("content"):
                reply = msg["content"]
                break

    return JSONResponse({
        "reply": reply,
        "mood":  _nia_state.mood,
        "energy": round(_nia_state.energy, 2),
        "turn":  _nia_state.turn_count,
    })


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    image_path = None
    if req.image_b64:
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.write(base64.b64decode(req.image_b64))
        tmp.close()
        image_path = tmp.name

    absence = _nia_state.estimate_absence()
    pending_thoughts = _thought_buffer.drain() if _thought_buffer.has_thoughts() else []
    _nia_state.touch()
    _mem.add("user", req.message)
    _history.append({"role": "user", "content": req.message})
    _nia_state.busy = True

    event_q: queue.SimpleQueue = queue.SimpleQueue()

    def _worker():
        try:
            for event in run_turn_streaming(
                _history, _mem,
                image=image_path,
                nia_state=_nia_state,
                absence=absence,
                pending_thoughts=pending_thoughts,
            ):
                event_q.put(event)
        except Exception as exc:
            event_q.put({"type": "error", "msg": str(exc)})
        finally:
            event_q.put(None)

    threading.Thread(target=_worker, daemon=True, name="nia-stream").start()

    async def _generate():
        loop = asyncio.get_event_loop()
        try:
            while True:
                event = await loop.run_in_executor(None, event_q.get)
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            _nia_state.busy = False
            if len(_history) > HISTORY_WINDOW:
                _history[:] = _history[-HISTORY_WINDOW:]
            if image_path:
                try:
                    os.unlink(image_path)
                except OSError:
                    pass

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/thoughts/poll")
async def thoughts_poll():
    item = _thought_buffer.drain_one()
    if not item:
        return JSONResponse({"thought": None})
    ts, text = item[0], item[1]
    return JSONResponse({"thought": text, "ts": ts})


@app.post("/capture")
async def capture():
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(_executor, vision.capture)
    if not path:
        return JSONResponse({"error": "capture failed"}, status_code=500)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return JSONResponse({"image_b64": b64, "mime": "image/jpeg"})


@app.get("/state")
async def state():
    return JSONResponse({
        "mood":   _nia_state.mood,
        "energy": round(_nia_state.energy, 2),
        "busy":   _nia_state.busy,
        "turn":   _nia_state.turn_count,
    })


@app.post("/learn")
async def learn_pdf(file: UploadFile = File(...), label: str = Form(None)):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse({"error": "Only PDF files are supported."}, status_code=400)
    label = label or file.filename
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(await file.read())
    tmp.close()

    def _ingest():
        import learn_pdf as lp
        return lp.ingest(tmp.name, label=label)

    try:
        loop = asyncio.get_event_loop()
        n = await loop.run_in_executor(_executor, _ingest)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    return JSONResponse({"chunks": n, "label": label,
                         "message": f"Nia now knows '{label}' — {n} chunks in memory."})


@app.get("/primer")
async def primer():
    return JSONResponse({"text": _PRIMER["content"]})


# ── UI HTML ───────────────────────────────────────────────────────────────────
_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nia</title>
<style>
  :root {
    --bg:       #080b0f;
    --surface:  #0f1318;
    --border:   #1c2230;
    --nia-bg:   #111820;
    --user-bg:  #141a24;
    --accent:   #c4882a;
    --accent2:  #e4a83e;
    --text:     #e4e0d4;
    --muted:    #666050;
    --mood-bg:  #141820;
    --thinking: #1a2230;
    --green:    #2d7d6f;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    font-size: 15px;
    height: 100dvh;
    display: flex;
    flex-direction: column;
  }

  header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  .avatar-sm {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid var(--accent);
  }

  .header-info { flex: 1; }
  .header-name { font-weight: 700; font-size: 16px; color: var(--text); letter-spacing: 0.03em; }
  .header-sub  { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }

  .mood-badge {
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 12px;
    background: var(--mood-bg);
    border: 1px solid var(--border);
    color: var(--accent2);
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-weight: 600;
    transition: all 0.4s;
  }

  .energy-bar { width: 60px; height: 3px; background: var(--border); border-radius: 2px; overflow: hidden; margin-top: 5px; }
  .energy-fill { height: 100%; background: var(--accent); border-radius: 2px; transition: width 0.8s ease; }

  #messages {
    flex: 1;
    overflow-y: auto;
    padding: 28px 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    scroll-behavior: smooth;
  }

  #messages::-webkit-scrollbar { width: 3px; }
  #messages::-webkit-scrollbar-track { background: transparent; }
  #messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .msg-row {
    display: flex;
    gap: 10px;
    max-width: 740px;
    align-self: flex-start;
    width: 100%;
  }
  .msg-row.user { align-self: flex-end; flex-direction: row-reverse; }

  .msg-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
    margin-top: 2px;
    border: 1.5px solid var(--accent);
  }
  .user .msg-avatar { border-color: #2a3040; }

  .bubble {
    padding: 12px 16px;
    border-radius: 16px;
    line-height: 1.6;
    max-width: 600px;
    word-break: break-word;
    white-space: pre-wrap;
  }

  .nia .bubble {
    background: var(--nia-bg);
    border: 1px solid var(--border);
    border-top-left-radius: 4px;
    color: var(--text);
  }

  .user .bubble {
    background: var(--user-bg);
    border: 1px solid #1e2840;
    border-top-right-radius: 4px;
    color: #b8c0cc;
  }

  .thinking-row { display: flex; gap: 10px; align-items: flex-start; }

  .dots {
    display: flex;
    gap: 5px;
    padding: 14px 18px;
    background: var(--thinking);
    border: 1px solid var(--border);
    border-radius: 16px;
    border-top-left-radius: 4px;
  }

  .dot {
    width: 7px; height: 7px;
    background: var(--accent);
    border-radius: 50%;
    animation: pulse 1.4s ease-in-out infinite;
  }
  .dot:nth-child(2) { animation-delay: 0.2s; }
  .dot:nth-child(3) { animation-delay: 0.4s; }

  @keyframes pulse {
    0%, 60%, 100% { opacity: 0.2; transform: scale(0.8); }
    30%           { opacity: 1;   transform: scale(1.1); }
  }

  .tool-note {
    font-size: 11px;
    color: var(--muted);
    padding: 3px 10px;
    margin-left: 42px;
    border-left: 2px solid var(--border);
    font-family: ui-monospace, 'SF Mono', monospace;
    letter-spacing: 0.02em;
  }

  .bubble img.preview {
    max-width: 220px;
    border-radius: 8px;
    margin-top: 6px;
    display: block;
    border: 1px solid var(--border);
  }

  #inputbar {
    display: flex;
    align-items: flex-end;
    gap: 10px;
    padding: 14px 20px;
    background: var(--surface);
    border-top: 1px solid var(--border);
    flex-shrink: 0;
  }

  #input {
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text);
    font-size: 15px;
    padding: 10px 14px;
    resize: none;
    outline: none;
    min-height: 42px;
    max-height: 160px;
    line-height: 1.5;
    font-family: inherit;
    transition: border-color 0.2s;
  }
  #input:focus { border-color: var(--accent); }
  #input::placeholder { color: var(--muted); }

  .icon-btn {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--muted);
    cursor: pointer;
    padding: 9px 11px;
    font-size: 18px;
    line-height: 1;
    transition: all 0.2s;
    flex-shrink: 0;
  }
  .icon-btn:hover { border-color: var(--accent); color: var(--accent2); }
  .icon-btn:disabled { opacity: 0.3; cursor: default; }

  #sendBtn {
    background: var(--accent);
    border-color: var(--accent);
    color: #000;
    font-size: 17px;
    font-weight: 700;
  }
  #sendBtn:hover { background: var(--accent2); border-color: var(--accent2); }

  #imgPreviewBar {
    display: none;
    align-items: center;
    gap: 10px;
    padding: 8px 20px;
    background: var(--surface);
    border-top: 1px solid var(--border);
  }
  #imgPreviewBar.visible { display: flex; }
  #imgThumb { width: 48px; height: 48px; object-fit: cover; border-radius: 8px; border: 1px solid var(--border); }
  #imgLabel { font-size: 12px; color: var(--muted); flex: 1; }
  #clearImg  { background: none; border: none; color: var(--muted); font-size: 18px; cursor: pointer; }
  #clearImg:hover { color: #ef4444; }
  #fileInput { display: none; }

  .sys-msg {
    text-align: center;
    font-size: 11px;
    color: var(--muted);
    padding: 4px 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
</style>
</head>
<body>

<header>
  <img class="avatar-sm" src="/static/nia.png" alt="Nia" onerror="this.style.display='none'">
  <div class="header-info">
    <div class="header-name">Nia</div>
    <div class="header-sub">Minister of Verdicts · Anthos Intelligence</div>
  </div>
  <div style="text-align:right">
    <div class="mood-badge" id="moodBadge">focused</div>
    <div class="energy-bar"><div class="energy-fill" id="energyFill" style="width:100%"></div></div>
  </div>
</header>

<div id="messages">
  <div class="sys-msg">Running locally — no data leaves this machine.</div>
</div>

<div id="imgPreviewBar">
  <img id="imgThumb" src="" alt="preview">
  <span id="imgLabel">Document attached</span>
  <button id="clearImg" title="Remove">✕</button>
</div>

<div id="inputbar">
  <button class="icon-btn" id="cameraBtn" title="Capture / scan document">📄</button>
  <label class="icon-btn" for="fileInput" title="Attach document or image">🖼️</label>
  <input type="file" id="fileInput" accept="image/*,.pdf">
  <textarea id="input" placeholder="What's your situation?" rows="1"></textarea>
  <button class="icon-btn" id="sendBtn" title="Send (Enter)">➤</button>
</div>

<script>
const AVATAR = "/static/nia.png";
const msgs   = document.getElementById("messages");
const input  = document.getElementById("input");
const send   = document.getElementById("sendBtn");

let pendingImage = null;
let waiting = false;

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
});
input.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMsg(); }
});
send.addEventListener("click", sendMsg);

document.getElementById("fileInput").addEventListener("change", e => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => setImage(ev.target.result, file.type);
  reader.readAsDataURL(file);
  e.target.value = "";
});
document.getElementById("clearImg").addEventListener("click", () => {
  pendingImage = null;
  document.getElementById("imgPreviewBar").classList.remove("visible");
  document.getElementById("imgThumb").src = "";
});
document.getElementById("cameraBtn").addEventListener("click", async () => {
  document.getElementById("cameraBtn").disabled = true;
  try {
    const r = await fetch("/capture", { method: "POST" });
    const d = await r.json();
    if (d.error) { appendSys("Capture failed: " + d.error); return; }
    setImage("data:" + d.mime + ";base64," + d.image_b64, d.mime, d.image_b64);
  } finally {
    document.getElementById("cameraBtn").disabled = false;
  }
});

function setImage(dataUrl, mime, b64override) {
  const b64 = b64override || dataUrl.split(",")[1];
  pendingImage = { b64, dataUrl };
  document.getElementById("imgThumb").src = dataUrl;
  document.getElementById("imgLabel").textContent = "Document / image ready";
  document.getElementById("imgPreviewBar").classList.add("visible");
}

// ── streaming send ────────────────────────────────────────────────────────────
async function sendMsg() {
  const text = input.value.trim();
  if (!text && !pendingImage) return;
  if (waiting) return;

  const msg = text || "(document)";
  const img = pendingImage;
  pendingImage = null;
  document.getElementById("imgPreviewBar").classList.remove("visible");
  input.value = "";
  input.style.height = "auto";

  appendUser(msg, img?.dataUrl);
  const thinkingEl = appendThinking();
  setWaiting(true);

  let niaBubble = null;
  let buffer    = "";

  try {
    const body = { message: msg };
    if (img) body.image_b64 = img.b64;

    const r = await fetch("/chat/stream", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(body),
    });

    if (!r.ok) {
      thinkingEl.remove();
      appendNia("(error " + r.status + ")");
      return;
    }

    const reader  = r.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        let event;
        try { event = JSON.parse(line.slice(6)); } catch { continue; }

        if (event.type === "tool") {
          if (!niaBubble) thinkingEl.remove();
          appendToolNote(friendlyTool(event.name));
        } else if (event.type === "chunk") {
          if (!niaBubble) {
            thinkingEl.remove();
            niaBubble = appendNiaStreaming();
          }
          appendChunk(niaBubble, event.text);
        } else if (event.type === "done") {
          updateState(event.mood, event.energy);
        } else if (event.type === "error") {
          if (!niaBubble) thinkingEl.remove();
          appendNia("(error: " + event.msg + ")");
        }
      }
    }
  } catch (err) {
    thinkingEl.remove();
    appendNia("(connection error — is the server running?)");
  } finally {
    setWaiting(false);
    if (!niaBubble) thinkingEl.remove();
  }
}

function friendlyTool(name) {
  return ({
    web_search:     "researching your situation",
    read_article:   "reading that source",
    remember_fact:  "saving to your file",
    add_goal:       "tracking your next step",
    complete_goal:  "updating your progress",
    journal_entry:  "writing to journal",
  })[name] || name.replace(/_/g, " ");
}

// ── DOM helpers ───────────────────────────────────────────────────────────────
function appendUser(text, imgDataUrl) {
  const row = document.createElement("div");
  row.className = "msg-row user";

  const av = document.createElement("div");
  av.style.cssText = "width:32px;height:32px;border-radius:50%;background:#141a24;border:1.5px solid #2a3040;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:16px;margin-top:2px;";
  av.textContent = "🧑";

  const bub = document.createElement("div");
  bub.className = "bubble";
  if (imgDataUrl) {
    const im = document.createElement("img");
    im.src = imgDataUrl;
    im.className = "preview";
    bub.appendChild(im);
  }
  if (text && text !== "(document)") {
    if (imgDataUrl) bub.appendChild(document.createElement("br"));
    const t = document.createElement("span");
    t.textContent = text;
    bub.appendChild(t);
  }
  row.append(bub, av);
  msgs.appendChild(row);
  scrollDown();
}

function appendNia(text) {
  const row = document.createElement("div");
  row.className = "msg-row nia";
  const av = document.createElement("img");
  av.className = "msg-avatar";
  av.src = AVATAR;
  av.onerror = () => { av.style.display = "none"; };
  const bub = document.createElement("div");
  bub.className = "bubble";
  bub.textContent = text;
  row.append(av, bub);
  msgs.appendChild(row);
  scrollDown();
}

function appendNiaStreaming() {
  const row = document.createElement("div");
  row.className = "msg-row nia";
  const av = document.createElement("img");
  av.className = "msg-avatar";
  av.src = AVATAR;
  av.onerror = () => { av.style.display = "none"; };
  const bub = document.createElement("div");
  bub.className = "bubble";
  bub._fullText = "";
  row.append(av, bub);
  msgs.appendChild(row);
  scrollDown();
  return bub;
}

function appendChunk(bubble, text) {
  bubble._fullText += text;
  bubble.textContent = bubble._fullText;
  scrollDown();
}

function appendToolNote(label) {
  const el = document.createElement("div");
  el.className = "tool-note";
  el.textContent = "↳ " + label + "…";
  msgs.appendChild(el);
  scrollDown();
}

function appendThinking() {
  const row = document.createElement("div");
  row.className = "msg-row nia thinking-row";
  const av = document.createElement("img");
  av.className = "msg-avatar";
  av.src = AVATAR;
  av.onerror = () => { av.style.display = "none"; };
  const dots = document.createElement("div");
  dots.className = "dots";
  for (let i = 0; i < 3; i++) {
    const d = document.createElement("div");
    d.className = "dot";
    dots.appendChild(d);
  }
  row.append(av, dots);
  msgs.appendChild(row);
  scrollDown();
  return row;
}

function appendSys(text) {
  const el = document.createElement("div");
  el.className = "sys-msg";
  el.textContent = text;
  msgs.appendChild(el);
  scrollDown();
}

function scrollDown() { msgs.scrollTop = msgs.scrollHeight; }

function setWaiting(v) {
  waiting = v;
  send.disabled = v;
  input.disabled = v;
}

function updateState(mood, energy) {
  document.getElementById("moodBadge").textContent = mood.replace("_", " ");
  document.getElementById("energyFill").style.width = (energy * 100) + "%";
}

// ── state poll (30s) ──────────────────────────────────────────────────────────
setInterval(async () => {
  try {
    const r = await fetch("/state");
    const d = await r.json();
    if (!waiting) updateState(d.mood, d.energy);
  } catch {}
}, 30_000);

// ── thought poll (2 min) ──────────────────────────────────────────────────────
setInterval(async () => {
  if (waiting) return;
  try {
    const r = await fetch("/thoughts/poll");
    const d = await r.json();
    if (d.thought) appendNia(d.thought);
  } catch {}
}, 120_000);

// ── load primer ───────────────────────────────────────────────────────────────
fetch("/primer").then(r => r.json()).then(d => appendNia(d.text));
input.focus();
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("Nia web interface → http://localhost:3100")
    uvicorn.run(app, host="0.0.0.0", port=3100, log_level="warning")
