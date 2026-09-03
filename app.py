"""
app.py — Nia web interface.

    pip install fastapi uvicorn
    python app.py

Runs on http://localhost:8000
Deployable to Render, Railway, or Fly.io as-is.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from nia.model import ModelUnavailable, get_client
from agents.nia.agent import NiaAgent
from agents.nia.intake import Domain, Urgency
from nia import privacy

app = FastAPI(title="Nia", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Model selection: NIA_MODEL env var controls backend
# "ollama" (default local), "claude" (API), "bedrock" (AWS Lambda)
_model_name = os.environ.get("NIA_MODEL", "ollama")

def _probe_ollama() -> bool:
    """Quick check — is Ollama reachable? Fails in <2s if not."""
    import urllib.request, urllib.error
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return True
    except Exception:
        return False

_ollama_available = _model_name == "ollama" and _probe_ollama()

def _get_agent():
    try:
        if _model_name == "ollama" and not _ollama_available:
            raise ModelUnavailable("Ollama not running")
        client = get_client(_model_name)
    except ModelUnavailable:
        client = None
    return NiaAgent(client)


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_input = (body.get("message") or "").strip()
    if not user_input:
        return JSONResponse({"error": "empty message"}, status_code=400)

    privacy.scrub_shared_dir()
    agent = _get_agent()

    try:
        situation = agent.intake(user_input)

        tags = [situation.domain.value]
        if situation.urgency == Urgency.CRISIS:
            tags.append("CRISIS")
        if situation.domain == Domain.IMMIGRATION:
            tags.append("max-privacy")

        responses = agent.triage(situation)
        final = agent.verdict(situation, responses)

        return JSONResponse({
            "reply": final,
            "domain": situation.domain.value,
            "urgency": situation.urgency.value,
            "squad": situation.squad_assignment,
            "tags": tags,
            "crisis": situation.urgency == Urgency.CRISIS,
            "immigration": situation.domain == Domain.IMMIGRATION,
        })
    finally:
        agent.close()
        privacy.scrub_shared_dir()


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nia — Intelligence for the People</title>
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #13131a;
    --border: #1e1e2e;
    --accent: #7c3aed;
    --accent2: #a78bfa;
    --text: #e2e8f0;
    --muted: #64748b;
    --crisis: #ef4444;
    --safe: #22c55e;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100dvh;
    display: flex;
    flex-direction: column;
  }
  header {
    padding: 16px 24px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
    background: var(--surface);
  }
  .logo {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 16px; color: white;
  }
  header h1 { font-size: 18px; font-weight: 700; letter-spacing: 0.05em; }
  header p { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .privacy-badge {
    margin-left: auto;
    font-size: 11px;
    color: var(--safe);
    border: 1px solid var(--safe);
    border-radius: 20px;
    padding: 3px 10px;
    opacity: 0.8;
  }
  #messages {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .welcome {
    max-width: 600px;
    margin: auto;
    text-align: center;
    padding: 40px 20px;
  }
  .welcome h2 { font-size: 24px; font-weight: 700; margin-bottom: 12px; }
  .welcome p { color: var(--muted); line-height: 1.7; font-size: 15px; }
  .domains {
    display: flex; flex-wrap: wrap; gap: 8px;
    justify-content: center; margin-top: 24px;
  }
  .domain-pill {
    font-size: 12px; color: var(--accent2);
    border: 1px solid var(--border);
    border-radius: 20px; padding: 4px 12px;
    background: var(--surface);
  }
  .msg { display: flex; gap: 12px; max-width: 760px; width: 100%; }
  .msg.user { flex-direction: row-reverse; margin-left: auto; }
  .avatar {
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 700; flex-shrink: 0;
  }
  .msg.nia .avatar { background: linear-gradient(135deg, var(--accent), var(--accent2)); color: white; }
  .msg.user .avatar { background: var(--border); color: var(--muted); }
  .bubble {
    padding: 12px 16px;
    border-radius: 16px;
    line-height: 1.65;
    font-size: 14px;
    max-width: calc(100% - 44px);
  }
  .msg.nia .bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    border-top-left-radius: 4px;
    white-space: pre-wrap;
  }
  .msg.user .bubble {
    background: var(--accent);
    border-top-right-radius: 4px;
    color: white;
  }
  .tags { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
  .tag {
    font-size: 10px; padding: 2px 8px;
    border-radius: 20px; border: 1px solid var(--border);
    color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em;
  }
  .tag.crisis { color: var(--crisis); border-color: var(--crisis); }
  .tag.privacy { color: var(--safe); border-color: var(--safe); }
  .crisis-banner {
    background: rgba(239,68,68,0.1);
    border: 1px solid var(--crisis);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    color: var(--crisis);
    margin-top: 8px;
  }
  footer {
    padding: 16px 24px;
    border-top: 1px solid var(--border);
    background: var(--surface);
  }
  .input-row {
    display: flex; gap: 10px;
    max-width: 760px; margin: 0 auto;
  }
  textarea {
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text);
    padding: 12px 16px;
    font-size: 14px;
    resize: none;
    min-height: 48px;
    max-height: 120px;
    font-family: inherit;
    line-height: 1.5;
    outline: none;
    transition: border-color 0.2s;
  }
  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: var(--muted); }
  button {
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0 20px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
    white-space: nowrap;
  }
  button:hover { opacity: 0.85; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  .disclaimer {
    text-align: center;
    font-size: 11px;
    color: var(--muted);
    margin-top: 8px;
    max-width: 760px;
    margin-left: auto; margin-right: auto;
  }
  .typing { display: flex; gap: 4px; padding: 4px 0; }
  .typing span {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--muted);
    animation: bounce 1.2s infinite;
  }
  .typing span:nth-child(2) { animation-delay: 0.2s; }
  .typing span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bounce {
    0%,80%,100% { transform: translateY(0); }
    40% { transform: translateY(-6px); }
  }
</style>
</head>
<body>
<header>
  <div class="logo">N</div>
  <div>
    <h1>NIA</h1>
    <p>Intelligence for the People</p>
  </div>
  <span class="privacy-badge">&#x25CF; Nothing is saved</span>
</header>

<div id="messages">
  <div class="welcome">
    <h2>Tell me what's going on.</h2>
    <p>I'm here for healthcare, housing, employment, education, immigration, and economic justice. Speak plainly — in your own words. Nothing you share is stored.</p>
    <div class="domains">
      <span class="domain-pill">Healthcare</span>
      <span class="domain-pill">Housing</span>
      <span class="domain-pill">Employment</span>
      <span class="domain-pill">Education</span>
      <span class="domain-pill">Immigration</span>
      <span class="domain-pill">Economic Justice</span>
    </div>
  </div>
</div>

<footer>
  <div class="input-row">
    <textarea id="input" placeholder="Describe your situation..." rows="1"></textarea>
    <button id="send">Send</button>
  </div>
  <p class="disclaimer">Nia is not a lawyer. In emergencies, call 911. Immigration situations never leave your device.</p>
</footer>

<script>
const messages = document.getElementById('messages');
const input = document.getElementById('input');
const send = document.getElementById('send');

function clearWelcome() {
  const w = messages.querySelector('.welcome');
  if (w) w.remove();
}

function addMsg(role, content, meta) {
  clearWelcome();
  const wrap = document.createElement('div');
  wrap.className = `msg ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = role === 'nia' ? 'N' : 'Y';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = content;

  if (meta) {
    if (meta.crisis) {
      const banner = document.createElement('div');
      banner.className = 'crisis-banner';
      banner.textContent = '⚠ If anyone is in immediate danger, call 911 first.';
      bubble.appendChild(banner);
    }
    if (meta.tags && meta.tags.length) {
      const tags = document.createElement('div');
      tags.className = 'tags';
      meta.tags.forEach(t => {
        const tag = document.createElement('span');
        tag.className = 'tag' + (t === 'CRISIS' ? ' crisis' : t === 'max-privacy' ? ' privacy' : '');
        tag.textContent = t;
        tags.appendChild(tag);
      });
      bubble.appendChild(tags);
    }
  }

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return wrap;
}

function addTyping() {
  clearWelcome();
  const wrap = document.createElement('div');
  wrap.className = 'msg nia';
  wrap.id = 'typing';

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = 'N';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
}

function removeTyping() {
  const t = document.getElementById('typing');
  if (t) t.remove();
}

async function submit() {
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  input.style.height = 'auto';
  send.disabled = true;

  addMsg('user', text);
  addTyping();

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    removeTyping();
    if (data.error) {
      addMsg('nia', 'Something went wrong. Please try again.');
    } else {
      addMsg('nia', data.reply, data);
    }
  } catch {
    removeTyping();
    addMsg('nia', 'Could not reach the server. Check your connection.');
  }

  send.disabled = false;
  input.focus();
}

send.addEventListener('click', submit);
input.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
});
input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 120) + 'px';
});
</script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    print(f"\nNia running at http://localhost:{port}\n")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
