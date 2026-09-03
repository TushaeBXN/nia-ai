"""
Credit Law Tool — Nia's verified credit/debt knowledge base.

Returns real FCRA/FDCPA citations, SOL by state, bureau contacts,
and dispute strategy — no hallucination, no internet needed.

Usage:
    python -m tools.credit_law charge-off
    python -m tools.credit_law sol --state TX
    python -m tools.credit_law bureaus
    python -m tools.credit_law dispute --type verification
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── Real FCRA/FDCPA citations ─────────────────────────────────────────────────

LAWS = {
    "fcra_611": {
        "citation": "15 U.S.C. § 1681i",
        "name": "FCRA Section 611 — Dispute Procedure",
        "summary": (
            "You have the right to dispute any inaccurate or unverifiable information "
            "on your credit report. The bureau must investigate within 30 days (45 days "
            "if you submit additional evidence). If they cannot verify the item, it MUST "
            "be deleted. They cannot simply 'confirm' it without documented proof."
        ),
        "key_rights": [
            "Bureau must complete investigation within 30 days of receiving your dispute",
            "Must notify the furnisher (the creditor/collector) of your dispute",
            "If furnisher cannot provide verification, item must be removed",
            "You must receive written results of the investigation",
            "You can request the method of verification they used",
        ],
    },
    "fcra_623": {
        "citation": "15 U.S.C. § 1681s-2",
        "name": "FCRA Section 623 — Furnisher Duties",
        "summary": (
            "Creditors and collectors (furnishers) who report to credit bureaus have "
            "legal duties. They cannot report information they know is inaccurate. "
            "After you dispute, they must conduct their own investigation."
        ),
        "key_rights": [
            "Furnisher must investigate a disputed item — they cannot just rubber-stamp their original report",
            "If they find the item is inaccurate, they must correct it with ALL bureaus they reported to",
            "You can dispute directly with the furnisher — not just with the bureau",
        ],
    },
    "fcra_605": {
        "citation": "15 U.S.C. § 1681c",
        "name": "FCRA Section 605 — Time Limits on Negative Items",
        "summary": (
            "Most negative items can only stay on your report for 7 years from the "
            "date of first delinquency (DOFD) — NOT from the date of last activity. "
            "Bankruptcies (Chapter 7) stay 10 years."
        ),
        "key_rights": [
            "Charge-offs: 7 years from DOFD",
            "Collections: 7 years from DOFD of the original account",
            "Late payments: 7 years from the date of the late payment",
            "Chapter 7 bankruptcy: 10 years",
            "Chapter 13 bankruptcy: 7 years",
            "Hard inquiries: 2 years",
            "Judgments: 7 years (or SOL, whichever is longer, in some states)",
        ],
    },
    "fdcpa_809": {
        "citation": "15 U.S.C. § 1692g",
        "name": "FDCPA Section 809 — Debt Validation",
        "summary": (
            "When a debt collector contacts you, you have 30 days to request validation "
            "of the debt in writing. They must stop all collection activity until they "
            "send you verification. This is one of your most powerful rights."
        ),
        "key_rights": [
            "Send debt validation letter within 30 days of first contact",
            "Collector must cease ALL collection activity until validation is provided",
            "Validation must include: amount, original creditor name, and proof they own/can collect",
            "If they cannot validate, they must stop collecting and remove from credit report",
        ],
    },
    "fdcpa_805": {
        "citation": "15 U.S.C. § 1692c",
        "name": "FDCPA Section 805 — Cease and Desist",
        "summary": (
            "You can send a written cease and desist letter to stop a debt collector "
            "from contacting you. They may only contact you once more to confirm they "
            "are stopping or to notify you of a specific action (like a lawsuit)."
        ),
        "key_rights": [
            "Collector MUST stop all contact after receiving written cease and desist",
            "One final contact is permitted — only to confirm they're stopping",
            "Violations of this section can result in statutory damages of $1,000 per violation",
        ],
    },
}

# Metro 2 compliance — the reporting format creditors must use
METRO2 = {
    "summary": (
        "Metro 2 is the standard format all furnishers must use when reporting to bureaus. "
        "Errors in Metro 2 compliance — wrong field values, incorrect dates, missing data — "
        "are a valid basis for dispute and deletion."
    ),
    "common_violations": [
        "Date of First Delinquency (DOFD) reported incorrectly — resets the 7-year clock illegally",
        "Account reported as open when it's been closed",
        "Balance not updated after payment or settlement",
        "Duplicate tradeline from original creditor AND debt collector for same debt",
        "Wrong account status code (e.g., '97' charge-off vs '64' collection)",
        "Payment history fields don't match the account history",
    ],
    "dispute_language": (
        "This tradeline contains Metro 2 format violations and is therefore inaccurate "
        "under 15 U.S.C. § 1681e(b), which requires bureaus to follow reasonable procedures "
        "for maximum accuracy. Please delete this item immediately."
    ),
}

# ── Statute of Limitations by state ──────────────────────────────────────────
# SOL = how long a creditor can SUE you to collect. After SOL, it's "time-barred."
# SOL does NOT equal how long it stays on your credit report (that's always 7 years FCRA).

SOL_BY_STATE = {
    "AL": {"years": 6, "type": "Written contract"},
    "AK": {"years": 3, "type": "Written contract"},
    "AZ": {"years": 6, "type": "Written contract"},
    "AR": {"years": 5, "type": "Written contract"},
    "CA": {"years": 4, "type": "Written contract"},
    "CO": {"years": 6, "type": "Written contract"},
    "CT": {"years": 6, "type": "Written contract"},
    "DE": {"years": 3, "type": "Written contract"},
    "FL": {"years": 5, "type": "Written contract"},
    "GA": {"years": 6, "type": "Written contract"},
    "HI": {"years": 6, "type": "Written contract"},
    "ID": {"years": 5, "type": "Written contract"},
    "IL": {"years": 5, "type": "Written contract"},
    "IN": {"years": 6, "type": "Written contract"},
    "IA": {"years": 5, "type": "Written contract"},
    "KS": {"years": 5, "type": "Written contract"},
    "KY": {"years": 5, "type": "Written contract"},
    "LA": {"years": 3, "type": "Written contract"},
    "ME": {"years": 6, "type": "Written contract"},
    "MD": {"years": 3, "type": "Written contract"},
    "MA": {"years": 6, "type": "Written contract"},
    "MI": {"years": 6, "type": "Written contract"},
    "MN": {"years": 6, "type": "Written contract"},
    "MS": {"years": 3, "type": "Written contract"},
    "MO": {"years": 5, "type": "Written contract"},
    "MT": {"years": 5, "type": "Written contract"},
    "NE": {"years": 5, "type": "Written contract"},
    "NV": {"years": 6, "type": "Written contract"},
    "NH": {"years": 3, "type": "Written contract"},
    "NJ": {"years": 6, "type": "Written contract"},
    "NM": {"years": 6, "type": "Written contract"},
    "NY": {"years": 3, "type": "Written contract"},
    "NC": {"years": 3, "type": "Written contract"},
    "ND": {"years": 6, "type": "Written contract"},
    "OH": {"years": 6, "type": "Written contract"},
    "OK": {"years": 5, "type": "Written contract"},
    "OR": {"years": 6, "type": "Written contract"},
    "PA": {"years": 4, "type": "Written contract"},
    "RI": {"years": 10, "type": "Written contract"},
    "SC": {"years": 3, "type": "Written contract"},
    "SD": {"years": 6, "type": "Written contract"},
    "TN": {"years": 6, "type": "Written contract"},
    "TX": {"years": 4, "type": "Written contract"},
    "UT": {"years": 6, "type": "Written contract"},
    "VT": {"years": 6, "type": "Written contract"},
    "VA": {"years": 5, "type": "Written contract"},
    "WA": {"years": 6, "type": "Written contract"},
    "WV": {"years": 10, "type": "Written contract"},
    "WI": {"years": 6, "type": "Written contract"},
    "WY": {"years": 8, "type": "Written contract"},
    "DC": {"years": 3, "type": "Written contract"},
}

# ── Credit bureaus + sub-bureaus ──────────────────────────────────────────────

BUREAUS = {
    "experian": {
        "name": "Experian",
        "dispute_online": "https://www.experian.com/disputes/main.html",
        "dispute_mail": "Experian, P.O. Box 4500, Allen, TX 75013",
        "dispute_phone": "1-888-397-3742",
        "notes": "Use certified mail with return receipt for paper disputes.",
    },
    "equifax": {
        "name": "Equifax",
        "dispute_online": "https://www.equifax.com/personal/credit-report-services/credit-dispute/",
        "dispute_mail": "Equifax Information Services LLC, P.O. Box 740256, Atlanta, GA 30374",
        "dispute_phone": "1-866-349-5191",
        "notes": "Equifax has the worst track record for online disputes — use certified mail.",
    },
    "transunion": {
        "name": "TransUnion",
        "dispute_online": "https://dispute.transunion.com",
        "dispute_mail": "TransUnion Consumer Solutions, P.O. Box 2000, Chester, PA 19016",
        "dispute_phone": "1-800-916-8800",
        "notes": "TransUnion online portal tends to be fastest for simple disputes.",
    },
    # Sub-bureaus
    "lexisnexis": {
        "name": "LexisNexis Risk Solutions",
        "type": "sub-bureau",
        "what_they_track": "Background checks, insurance claims, public records, address history",
        "dispute_online": "https://consumer.risk.lexisnexis.com/request",
        "dispute_phone": "1-800-456-6004",
        "notes": (
            "Most people don't know this one exists. Used by insurance companies and landlords. "
            "Get your free report first — it affects insurance rates and rental applications."
        ),
    },
    "chexsystems": {
        "name": "ChexSystems",
        "type": "sub-bureau",
        "what_they_track": "Banking history — bounced checks, overdrafts, account closures",
        "dispute_online": "https://www.chexsystems.com/security-freeze/place-freeze",
        "dispute_phone": "1-800-428-9623",
        "notes": (
            "If you've been denied a bank account, ChexSystems is probably why. "
            "Negative items stay for 5 years. You can request your free report once per year."
        ),
    },
    "early_warning": {
        "name": "Early Warning Services (EWS / Zelle owner)",
        "type": "sub-bureau",
        "what_they_track": "Banking fraud alerts, account verification — used by major banks",
        "dispute_contact": "Early Warning Services, LLC, 16552 N. 90th Street, Scottsdale, AZ 85260",
        "dispute_phone": "1-800-745-1986",
        "notes": (
            "JPMorgan Chase, Bank of America, Wells Fargo, and others use EWS. "
            "If you've been flagged for fraud (even incorrectly), this blocks you from major banks."
        ),
    },
    "nctue": {
        "name": "NCTUE (National Consumer Telecom & Utilities Exchange)",
        "type": "sub-bureau",
        "what_they_track": "Utility and telecom payment history — phone, electric, cable",
        "dispute_phone": "1-866-349-5185",
        "notes": (
            "Affects your ability to get phone service and utilities without a deposit. "
            "Operated by Equifax. Dispute through Equifax."
        ),
    },
    "innovis": {
        "name": "Innovis",
        "type": "sub-bureau",
        "what_they_track": "Fourth major credit bureau — used by some lenders and marketers",
        "dispute_online": "https://www.innovis.com/personal/creditDispute",
        "dispute_mail": "Innovis Consumer Assistance, P.O. Box 26, Pittsburgh, PA 15230",
        "dispute_phone": "1-800-540-2505",
        "notes": (
            "Often overlooked. Some lenders and insurers use Innovis. "
            "Free annual report available at innovis.com."
        ),
    },
}

# ── Dispute strategies ────────────────────────────────────────────────────────

STRATEGIES = {
    "verification": {
        "name": "Verification Dispute (Section 611)",
        "best_for": "Any item you believe is inaccurate or cannot be proven accurate",
        "law": "15 U.S.C. § 1681i",
        "steps": [
            "Pull your credit report — identify the exact item, the furnisher name, and the account number",
            "Draft a dispute letter citing 15 U.S.C. § 1681i demanding verification",
            "Send via CERTIFIED MAIL with return receipt to the bureau(s) reporting it",
            "Keep copies of everything — the letter, the certified mail receipt, the green card when it returns",
            "Bureau has 30 days to investigate and respond",
            "If they 'verify' it: request the Method of Verification in writing (your right under § 1681i(a)(7))",
            "If they delete it: get written confirmation and check all three bureaus",
        ],
        "warning": (
            "Do NOT dispute online for serious items — online disputes give bureaus a checkbox "
            "system that makes it easy to click 'verified.' Certified mail creates a paper trail "
            "and starts a 30-day clock they must legally meet."
        ),
    },
    "debt_validation": {
        "name": "Debt Validation (Section 809)",
        "best_for": "Collection accounts — when a collector has contacted you or is reporting",
        "law": "15 U.S.C. § 1692g",
        "steps": [
            "Within 30 days of first contact, send a debt validation letter via certified mail",
            "Demand: name of original creditor, amount owed with breakdown, proof they own/can collect",
            "Collector must STOP all collection activity until they respond",
            "If they cannot validate, demand removal from all credit bureaus",
            "If they keep calling anyway: each violation is $1,000 in statutory damages — document it",
        ],
        "warning": (
            "DO NOT make any payment — not even $1 — until you receive full validation. "
            "A payment can restart the Statute of Limitations on an old debt."
        ),
    },
    "statute_of_limitations": {
        "name": "Time-Barred Debt Defense",
        "best_for": "Old debts a collector is trying to collect or re-report",
        "law": "FCRA 15 U.S.C. § 1681c + state SOL law",
        "steps": [
            "Identify the Date of First Delinquency (DOFD) — this is when the account first went past due and never recovered",
            "If DOFD + 7 years has passed, it is past the FCRA reporting window and must be deleted",
            "If collector's SOL in your state has expired, the debt is legally uncollectible (time-barred)",
            "Send a letter to the bureau citing 15 U.S.C. § 1681c and demanding deletion",
            "NEVER acknowledge the debt in writing or verbally — this can restart the SOL in some states",
            "If being sued for a time-barred debt: show up to court and raise SOL as an affirmative defense",
        ],
        "warning": (
            "Paying or even acknowledging a time-barred debt in writing can restart the SOL "
            "in some states, making you legally liable again. Know your state's rules first."
        ),
    },
    "charge_off": {
        "name": "Charge-Off Strategy",
        "best_for": "Charge-offs reported by original creditor, with or without collection",
        "law": "15 U.S.C. § 1681c, § 1681i, § 1681s-2",
        "steps": [
            "Confirm the DOFD — charge-off must be deleted 7 years from DOFD, not from charge-off date",
            "Check if both the original creditor AND a collector are reporting the same debt — this is a Metro 2 duplicate violation",
            "Dispute the charge-off citing Metro 2 compliance issues if the DOFD or balance is wrong",
            "For pay-for-delete: contact the creditor IN WRITING and offer to pay in exchange for deletion — get it in writing before paying",
            "Know that the three bureaus formally ended pay-for-delete agreements with major creditors in 2022 — some smaller creditors still do it",
        ],
        "warning": (
            "Paying a charge-off does NOT remove it from your report. It changes status to "
            "'paid charge-off' — which still hurts. Only pay if you get deletion in writing first, "
            "or if you need to clear it for a specific loan application."
        ),
    },
}


# ── Public functions ──────────────────────────────────────────────────────────

def get_law(key: str) -> dict:
    """Return a specific law entry by key."""
    return LAWS.get(key, {})


def get_all_laws() -> dict:
    return LAWS


def get_sol(state: str) -> dict:
    """Return SOL for a state (2-letter code)."""
    return SOL_BY_STATE.get(state.upper(), {})


def get_bureau(name: str) -> dict:
    """Return bureau/sub-bureau info."""
    return BUREAUS.get(name.lower().replace(" ", "_"), {})


def get_all_bureaus(include_sub: bool = True) -> dict:
    if include_sub:
        return BUREAUS
    return {k: v for k, v in BUREAUS.items() if "type" not in v}


def get_strategy(key: str) -> dict:
    """Return dispute strategy by key."""
    return STRATEGIES.get(key, {})


def analyze_situation(situation_text: str) -> dict:
    """
    Given a free-text description of a credit situation, return:
    - relevant laws
    - recommended strategy
    - relevant bureaus
    - key warnings
    """
    text = situation_text.lower()
    result = {
        "laws": [],
        "strategy": None,
        "bureaus": [],
        "warnings": [],
        "notes": [],
    }

    # Detect charge-off
    if "charge" in text and ("off" in text or "-off" in text):
        result["laws"].append(LAWS["fcra_605"])
        result["laws"].append(LAWS["fcra_611"])
        result["laws"].append(LAWS["fcra_623"])
        result["strategy"] = STRATEGIES["charge_off"]
        result["warnings"].append(
            "Paying a charge-off does NOT remove it. Get deletion in writing first."
        )

    # Detect collection / debt collector
    if any(w in text for w in ["collector", "collection", "debt collector", "collections"]):
        result["laws"].append(LAWS["fdcpa_809"])
        result["laws"].append(LAWS["fdcpa_805"])
        if result["strategy"] is None:
            result["strategy"] = STRATEGIES["debt_validation"]
        result["warnings"].append(
            "Do NOT pay anything until you receive full debt validation in writing."
        )

    # Detect old debt / SOL angle
    if any(w in text for w in ["old debt", "2019", "2018", "2017", "2016", "years ago", "statute"]):
        result["laws"].append(LAWS["fcra_605"])
        if result["strategy"] is None:
            result["strategy"] = STRATEGIES["statute_of_limitations"]
        result["notes"].append(
            "This debt may be past the 7-year FCRA reporting window. "
            "Identify the Date of First Delinquency to confirm."
        )

    # Detect dispute denial
    if any(w in text for w in ["denied", "deny", "denying", "verified", "investigation"]):
        result["laws"].append(LAWS["fcra_611"])
        result["notes"].append(
            "You have the right to request the Method of Verification "
            "(15 U.S.C. § 1681i(a)(7)) — demand it in writing."
        )
        if result["strategy"] is None:
            result["strategy"] = STRATEGIES["verification"]

    # Detect specific bureaus mentioned
    for bureau_key in ["experian", "equifax", "transunion"]:
        if bureau_key in text:
            result["bureaus"].append(BUREAUS[bureau_key])

    # Default: all three main bureaus if none detected
    if not result["bureaus"]:
        result["bureaus"] = [BUREAUS["experian"], BUREAUS["equifax"], BUREAUS["transunion"]]

    # De-dup laws by citation
    seen_citations = set()
    unique_laws = []
    for law in result["laws"]:
        if law.get("citation") not in seen_citations:
            seen_citations.add(law.get("citation"))
            unique_laws.append(law)
    result["laws"] = unique_laws

    # Default strategy if nothing matched
    if result["strategy"] is None:
        result["strategy"] = STRATEGIES["verification"]

    return result


def format_analysis(situation_text: str) -> str:
    """Human-readable credit law analysis for a given situation."""
    r = analyze_situation(situation_text)
    lines = []

    lines.append("── CREDIT LAW ANALYSIS ─────────────────────────────")

    if r["laws"]:
        lines.append("\nYOUR LEGAL RIGHTS:")
        for law in r["laws"]:
            lines.append(f"\n{law['citation']} — {law['name']}")
            lines.append(f"  {law['summary']}")

    if r["strategy"]:
        s = r["strategy"]
        lines.append(f"\nRECOMMENDED STRATEGY: {s['name']}")
        lines.append(f"Law: {s['law']}")
        lines.append("Steps:")
        for i, step in enumerate(s["steps"], 1):
            lines.append(f"  {i}. {step}")
        if s.get("warning"):
            lines.append(f"\n⚠ WARNING: {s['warning']}")

    if r["notes"]:
        lines.append("\nKEY NOTES:")
        for note in r["notes"]:
            lines.append(f"  • {note}")

    if r["warnings"]:
        lines.append("\nWARNINGS:")
        for w in r["warnings"]:
            lines.append(f"  ⚠ {w}")

    if r["bureaus"]:
        lines.append("\nWHERE TO DISPUTE:")
        for b in r["bureaus"]:
            lines.append(f"\n  {b['name']}")
            if b.get("dispute_mail"):
                lines.append(f"    Mail: {b['dispute_mail']}")
            if b.get("dispute_phone"):
                lines.append(f"    Phone: {b['dispute_phone']}")

    lines.append("\n────────────────────────────────────────────────────")
    lines.append("This is verified legal information, not legal advice.")
    lines.append("A nonprofit credit counselor or legal aid attorney can act on your behalf — free.")

    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    cmd = args[0].lower()

    if cmd == "bureaus":
        for k, b in BUREAUS.items():
            t = f" [{b.get('type', 'main bureau')}]" if "type" in b else ""
            print(f"\n{b['name']}{t}")
            if b.get("dispute_phone"):
                print(f"  Phone: {b['dispute_phone']}")
            if b.get("notes"):
                print(f"  Note: {b['notes']}")

    elif cmd == "sol":
        state = None
        if "--state" in args:
            state = args[args.index("--state") + 1].upper()
        if state:
            sol = get_sol(state)
            if sol:
                print(f"\nStatute of Limitations — {state}")
                print(f"  {sol['years']} years ({sol['type']})")
                print(f"  After {sol['years']} years from last payment/acknowledgment,")
                print(f"  a creditor CANNOT sue you to collect this debt.")
            else:
                print(f"State '{state}' not found.")
        else:
            print("\nStatute of Limitations by State (written contracts / credit card debt):\n")
            for state, sol in sorted(SOL_BY_STATE.items()):
                print(f"  {state}: {sol['years']} years")

    elif cmd == "dispute":
        dtype = "verification"
        if "--type" in args:
            dtype = args[args.index("--type") + 1]
        s = get_strategy(dtype)
        if s:
            print(f"\n{s['name']} — {s['law']}")
            print(f"\n{s['best_for']}\n")
            for i, step in enumerate(s["steps"], 1):
                print(f"  {i}. {step}")
            if s.get("warning"):
                print(f"\n⚠  {s['warning']}")
        else:
            print(f"Strategy '{dtype}' not found. Options: {', '.join(STRATEGIES.keys())}")

    elif cmd == "analyze":
        situation = " ".join(args[1:])
        if not situation:
            situation = input("Describe the credit situation: ")
        print(format_analysis(situation))

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: bureaus, sol, dispute, analyze")
        sys.exit(1)


if __name__ == "__main__":
    main()
