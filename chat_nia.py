#!/usr/bin/env python3
"""
Nia — The Minister of Verdicts
Chat interface
"""

import json
import sys
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "nia"

BANNER = """
╔══════════════════════════════════════════════════════════╗
║              N I A                                       ║
║        The Minister of Verdicts                          ║
║                                                          ║
║  "I do not answer questions. I issue depositions."       ║
║                                                          ║
║  Type your message. Type 'exit' or Ctrl+C to leave.     ║
╚══════════════════════════════════════════════════════════╝
"""

def stream_chat(messages):
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "stream": True,
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    full_response = ""
    try:
        with urllib.request.urlopen(req) as resp:
            for line in resp:
                line = line.decode().strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content", "")
                    print(chunk, end="", flush=True)
                    full_response += chunk
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
    except urllib.error.URLError as e:
        print(f"\n[Error connecting to Ollama: {e}]")
        print("Make sure Ollama is running: ollama serve")
        sys.exit(1)

    print()
    return full_response


def main():
    print(BANNER)
    history = []

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nNia: The work continues. Until next time.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            print("\nNia: The work continues. Until next time.")
            break

        history.append({"role": "user", "content": user_input})

        print("\nNia: ", end="", flush=True)
        response = stream_chat(history)

        if response:
            history.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
