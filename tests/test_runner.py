"""
Nia test runner — runs entirely offline (no model, no network).

Checks:
  1. Every scenario in tests/scenarios/ classifies to the expected
     domain and urgency (deterministic fallback classifier).
  2. The full pipeline (intake → triage → verdict) completes for every
     scenario and the verdict contains real resources.
  3. PRIVACY: immigration scenarios write NOTHING to disk; other
     scenarios' coordination files are wiped at session end.
  4. The resource directory has 20+ orgs and every domain has matches.
  5. The situation documenter produces every required section.

Usage:  python -m tests.test_runner
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from agents.nia.agent import NiaAgent
from agents.nia.intake import Domain, classify_fallback, intake
from nia import config
from tools.document_generator import generate
from tools.resource_router import load_directory, match

PASS, FAIL = "PASS", "FAIL"
failures = []


def check(name: str, ok: bool, detail: str = ""):
    print(f"  [{PASS if ok else FAIL}] {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(f"{name}: {detail}")


def load_scenarios():
    scenarios = []
    for path in sorted((REPO / "tests" / "scenarios").glob("*.md")):
        text = path.read_text()
        header, _, body = text.partition("\n---\n")
        domain = re.search(r"expected_domain:\s*(\w+)", header).group(1)
        urgency = re.search(r"expected_urgency:\s*(\w+)", header).group(1)
        scenarios.append((path.stem, domain, urgency, body.strip()))
    return scenarios


def shared_case_files():
    if not config.SHARED_DIR.exists():
        return []
    return [f for f in config.SHARED_DIR.iterdir() if f.name != ".gitkeep"]


def test_classification(scenarios):
    print("\n── Classification (offline fallback) ──")
    for name, domain, urgency, body in scenarios:
        result = classify_fallback(body)
        check(f"{name}: domain={domain}", result["domain"] == domain,
              f"got {result['domain']}")
        check(f"{name}: urgency={urgency}", result["urgency"] == urgency,
              f"got {result['urgency']}")


def test_pipeline_and_privacy(scenarios):
    print("\n── Full pipeline + privacy ──")
    for name, domain, urgency, body in scenarios:
        agent = NiaAgent(model_client=None)
        situation = agent.intake(body)
        responses = agent.triage(situation)
        final = agent.verdict(situation, responses)

        check(f"{name}: verdict produced", bool(final and len(final) > 100))
        check(f"{name}: verdict includes resources", "WHO CAN HELP" in final)

        leftovers = shared_case_files()
        if situation.domain == Domain.IMMIGRATION:
            check(f"{name}: MAX PRIVACY — nothing written to disk",
                  len(leftovers) == 0, f"found {[f.name for f in leftovers]}")
        else:
            check(f"{name}: coordination files written during session",
                  len(leftovers) > 0)

        agent.close()
        leftovers = shared_case_files()
        check(f"{name}: ZERO RETENTION — wiped after session",
              len(leftovers) == 0, f"found {[f.name for f in leftovers]}")


def test_resources():
    print("\n── Resource directory ──")
    orgs = load_directory()
    check(f"directory has 20+ organizations (found {len(orgs)})", len(orgs) >= 20)
    for org in orgs:
        check(f"{org['name']}: has website or phone",
              bool(org.get("website") or org.get("phone")))
    for domain in ("healthcare", "housing", "employment", "education",
                   "immigration", "economic", "discrimination"):
        matches = match(domain)
        check(f"domain '{domain}' has 3+ matches (found {len(matches)})",
              len(matches) >= 3)


def test_documenter():
    print("\n── Situation documenter ──")
    situation = intake(
        "My landlord in Georgia gave me an eviction notice after I "
        "complained about mold. I think it's because I'm Black."
    )
    doc = generate(situation, parties=["Landlord — J. Smith"],
                   actions_taken=["Complained about mold on June 3"])
    for section in ("Summary of the Situation", "Chronological Facts",
                    "Parties Involved", "Actions Taken So Far",
                    "Potential Legal Hooks", "not legal advice"):
        check(f"documenter includes '{section}'", section in doc)
    check("documenter picked up state=GA", situation.state == "GA")


def main():
    scenarios = load_scenarios()
    print(f"Nia offline test suite — {len(scenarios)} scenarios")
    test_classification(scenarios)
    test_pipeline_and_privacy(scenarios)
    test_resources()
    test_documenter()

    print("\n" + "=" * 50)
    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  ✗ {f}")
        sys.exit(1)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
