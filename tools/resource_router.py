"""
Resource Router (Phase 1)

Matches a situation's domain to organizations in the national directory
(knowledge/resources/national/*.json). No model, no network — reading a
directory should work on any machine, always.

Usage:
    python -m tools.resource_router housing
    python -m tools.resource_router immigration --limit 3
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nia import config


def load_directory() -> list:
    """All organizations from every national directory file."""
    orgs = []
    national = config.RESOURCES_DIR / "national"
    if not national.exists():
        return orgs
    for path in sorted(national.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        orgs.extend(data.get("organizations", []))
    # De-dup by name (an org may appear in more than one file someday)
    seen, unique = set(), []
    for org in orgs:
        if org["name"] not in seen:
            seen.add(org["name"])
            unique.append(org)
    return unique


def match(domain: str, limit: int = 5) -> list:
    """Organizations serving a domain — primary-domain matches first."""
    domain = str(domain).lower()
    primary, secondary = [], []
    for org in load_directory():
        domains = [d.lower() for d in org.get("domains", [])]
        if not domains:
            continue
        if domains[0] == domain:
            primary.append(org)
        elif domain in domains:
            secondary.append(org)
    return (primary + secondary)[:limit]


def format_org(org: dict) -> str:
    lines = [f"• {org['name']}"]
    if org.get("phone"):
        lines.append(f"    Call: {org['phone']}")
    if org.get("website"):
        lines.append(f"    Web:  {org['website']}")
    if org.get("what_they_help_with"):
        lines.append(f"    Helps with: {org['what_they_help_with']}")
    if org.get("eligibility"):
        lines.append(f"    Who: {org['eligibility']}")
    return "\n".join(lines)


def format_matches(domain: str, limit: int = 5) -> str:
    orgs = match(domain, limit)
    if not orgs:
        return f"No national organizations mapped for '{domain}' yet."
    return "\n\n".join(format_org(o) for o in orgs)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    limit = 5
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    if not args:
        print(__doc__)
        sys.exit(1)
    print(format_matches(args[0], limit))


if __name__ == "__main__":
    main()
