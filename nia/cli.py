"""
Nia — command-line interface.

    python -m nia.cli                 # local Ollama model (default: 'nia')
    python -m nia.cli --model claude  # Claude API (needs ANTHROPIC_API_KEY)
    python -m nia.cli --no-model      # deterministic offline mode

Privacy: zero retention. Coordination files are wiped when the session
ends; immigration situations never touch disk at all.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nia import privacy
from nia.memory import NiaMemory
from nia.model import ModelUnavailable, get_client
from agents.nia.agent import NiaAgent
from agents.nia.intake import Domain, Urgency

BANNER = """
╔══════════════════════════════════════════════════════════╗
║   N I A  —  Intelligence for the People                  ║
║                                                          ║
║   Healthcare · Housing · Employment · Education          ║
║   Immigration · Economic Justice                         ║
║                                                          ║
║   Tell me what's going on, in your own words.            ║
║   Nothing you share here is saved. Type 'exit' to leave. ║
╚══════════════════════════════════════════════════════════╝
"""


def build_model(args):
    if args.no_model:
        return None
    try:
        client = get_client(args.model)
        if args.model == "claude":
            print("[Note: using the Claude API — your words leave this machine.")
            print(" Immigration situations are handled locally-only regardless.]\n")
        return client
    except ModelUnavailable as e:
        print(f"[{e}]")
        print("[Continuing in offline mode — rights info and resources still work.]\n")
        return None


def main():
    parser = argparse.ArgumentParser(description="Nia — Intelligence for the People")
    parser.add_argument("--model", default="ollama",
                        help="'ollama' (default), 'claude', or an Ollama model name")
    parser.add_argument("--no-model", action="store_true",
                        help="Run deterministic offline mode (no AI model)")
    args = parser.parse_args()

    privacy.scrub_shared_dir()  # clean slate — no leftovers from a crashed run
    print(BANNER)

    model = build_model(args)
    agent = NiaAgent(model)
    mem = NiaMemory()

    # Show memory status on first run
    if mem.available():
        print("[Memory active — I'll remember what we work on across sessions.]\n")

    try:
        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "bye"):
                break

            situation = agent.intake(user_input)

            # Inject prior session context before triage
            if situation.domain != Domain.IMMIGRATION:  # privacy: never recall for immigration
                warm_up = mem.warm_up()
                if warm_up:
                    situation.documented_facts.insert(0, warm_up)

            print(f"\n[Understood: {situation.domain.value} · "
                  f"urgency {situation.urgency.value}"
                  + (f" · {situation.state}" if situation.state else "") + "]")
            if situation.domain == Domain.IMMIGRATION:
                print("[Maximum privacy mode: nothing in this conversation is "
                      "written to disk or sent to any cloud service.]")
            if situation.urgency == Urgency.CRISIS:
                print("[If anyone is in immediate danger, call 911 first.]")

            print("[Checking with the squad: "
                  + ", ".join(situation.squad_assignment) + " ...]\n")

            responses = agent.triage(situation)
            final = agent.verdict(situation, responses)
            print("Nia:", final)

            # Save this session to memory (skip immigration for privacy)
            if situation.domain != Domain.IMMIGRATION:
                mem.save_session(situation, final)

            print("\n[Want a summary you can hand to a lawyer or advocate? "
                  "Run: python -m tools.document_generator]")
    finally:
        agent.close()
        privacy.scrub_shared_dir()
        print("\nNia: Nothing from this session was kept. The work continues. "
              "Take care of yourself.")


if __name__ == "__main__":
    main()
