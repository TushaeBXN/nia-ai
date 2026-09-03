"""
Student Loan Tool — Nia's verified student loan knowledge base.

Covers PSLF, IDR plans, Teacher Loan Forgiveness, Borrower Defense,
for-profit school discharge, and payoff strategy — no hallucination.

Usage:
    python -m tools.student_loans pslf --years 4 --employer "City Hospital"
    python -m tools.student_loans idr --balance 45000 --income 38000 --family 2
    python -m tools.student_loans school --name "Full Sail University"
    python -m tools.student_loans forgiveness --type teacher
    python -m tools.student_loans analyze "I went to ITT Tech and owe 28000"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── PSLF knowledge ────────────────────────────────────────────────────────────

PSLF = {
    "name": "Public Service Loan Forgiveness",
    "law": "20 U.S.C. § 1087e(m)",
    "summary": (
        "After 10 years (120 payments) working full-time for a qualifying employer "
        "on an income-driven repayment plan, your remaining federal loan balance "
        "is forgiven TAX-FREE."
    ),
    "requirements": [
        "Work full-time (30+ hrs/wk) for a qualifying employer",
        "Have Direct Loans (FFEL/Perkins must be consolidated first)",
        "Be on a qualifying IDR plan (SAVE, IBR, PAYE, or ICR)",
        "Make 120 qualifying payments (doesn't have to be consecutive)",
        "Submit Employment Certification Form (ECF) every year",
    ],
    "qualifying_employers": [
        "Federal, state, local, or tribal government agencies",
        "501(c)(3) nonprofit organizations",
        "AmeriCorps or Peace Corps",
        "Public schools, public universities, public hospitals",
        "Other nonprofits providing qualifying public services",
    ],
    "non_qualifying": [
        "For-profit companies (even if doing public good)",
        "Labor unions and partisan political organizations",
        "Nonprofits that are NOT 501(c)(3)",
    ],
    "common_mistakes": [
        "Being on a graduated or extended repayment plan instead of IDR — those payments DON'T count",
        "Having FFEL loans instead of Direct Loans — must consolidate first",
        "Not submitting ECF annually — years of payments can be disputed later",
        "Working part-time (under 30 hrs/wk) — doesn't count",
        "Private loans — PSLF only covers federal loans",
    ],
    "steps": [
        "Confirm your loans are Direct Loans at studentaid.gov",
        "If you have FFEL loans, consolidate into a Direct Consolidation Loan (free at studentaid.gov)",
        "Enroll in an IDR plan — SAVE is currently the best for most borrowers",
        "Submit an Employment Certification Form (ECF) for EVERY employer, every year",
        "Track your qualifying payment count at studentaid.gov/manage-loans/repayment/pslf",
        "After 120 payments, submit the PSLF Application for Forgiveness",
    ],
    "waiver_note": (
        "The PSLF Waiver (2021-2022) allowed many previously non-qualifying payments to count. "
        "If you were denied PSLF before 2023, check if you qualify for an IDR Adjustment — "
        "some borrowers got credit for payments they didn't know counted."
    ),
}

# ── IDR Plans ─────────────────────────────────────────────────────────────────

IDR_PLANS = {
    "SAVE": {
        "name": "Saving on a Valuable Education (SAVE)",
        "formerly": "REPAYE",
        "payment_formula": "5% of discretionary income for undergrad loans, 10% for grad",
        "discretionary_income": "Income above 225% of federal poverty line",
        "forgiveness": "20 years (undergrad only) or 25 years (any grad loans)",
        "best_for": "Most borrowers — lowest payments for undergrad debt",
        "note": (
            "As of 2024-2026, SAVE has been subject to court challenges. "
            "Check studentaid.gov for current status before enrolling."
        ),
    },
    "IBR": {
        "name": "Income-Based Repayment (IBR)",
        "payment_formula": "10% of discretionary income (new borrowers after 7/1/2014), 15% (older)",
        "discretionary_income": "Income above 150% of federal poverty line",
        "forgiveness": "20 years (new borrowers) or 25 years (older borrowers)",
        "best_for": "Borrowers pursuing PSLF — widely accepted and legally stable",
        "note": "Most legally stable IDR plan — recommended if SAVE is in litigation.",
    },
    "PAYE": {
        "name": "Pay As You Earn (PAYE)",
        "payment_formula": "10% of discretionary income, never more than standard 10-yr payment",
        "discretionary_income": "Income above 150% of federal poverty line",
        "forgiveness": "20 years",
        "best_for": "New borrowers with high debt-to-income ratio",
        "note": "Must be a new borrower as of Oct 1, 2007 with a loan after Oct 1, 2011.",
    },
    "ICR": {
        "name": "Income-Contingent Repayment (ICR)",
        "payment_formula": "20% of discretionary income OR 12-year fixed payment, whichever is less",
        "discretionary_income": "Income above 100% of federal poverty line",
        "forgiveness": "25 years",
        "best_for": "Parent PLUS loan borrowers (only IDR plan available to them after consolidation)",
        "note": "Highest payments of all IDR plans — use only when no other plan is available.",
    },
}

# Federal poverty guidelines 2024 (lower 48 states) — used for IDR calculations
POVERTY_LINE_2024 = {
    1: 15060,
    2: 20440,
    3: 25820,
    4: 31200,
    5: 36580,
    6: 41960,
    7: 47340,
    8: 52720,
}


def poverty_line(family_size: int) -> float:
    if family_size <= 8:
        return POVERTY_LINE_2024.get(family_size, 15060)
    return 15060 + (family_size - 1) * 5380


def idr_payment(annual_income: float, family_size: int, plan: str = "SAVE") -> dict:
    """Calculate monthly IDR payment for a given plan."""
    fpl = poverty_line(family_size)

    if plan == "SAVE":
        discretionary = max(0, annual_income - (fpl * 2.25))
        monthly = (discretionary * 0.05) / 12  # undergrad rate
        forgiveness_years = 20
    elif plan in ("IBR", "PAYE"):
        discretionary = max(0, annual_income - (fpl * 1.5))
        monthly = (discretionary * 0.10) / 12
        forgiveness_years = 20
    elif plan == "ICR":
        discretionary = max(0, annual_income - fpl)
        monthly = (discretionary * 0.20) / 12
        forgiveness_years = 25
    else:
        discretionary = max(0, annual_income - (fpl * 1.5))
        monthly = (discretionary * 0.10) / 12
        forgiveness_years = 20

    return {
        "plan": plan,
        "monthly_payment": round(monthly, 2),
        "annual_payment": round(monthly * 12, 2),
        "forgiveness_years": forgiveness_years,
        "discretionary_income": round(discretionary, 2),
    }


# ── Teacher Loan Forgiveness ──────────────────────────────────────────────────

TEACHER_FORGIVENESS = {
    "name": "Teacher Loan Forgiveness",
    "law": "20 U.S.C. § 1078-10",
    "max_amount": "$17,500 (math/science/special ed) or $5,000 (other subjects)",
    "requirements": [
        "Teach full-time for 5 complete consecutive academic years",
        "At a low-income school (Title I school — check TCLI directory)",
        "In a subject shortage area OR special education",
        "Have Direct Subsidized/Unsubsidized loans or Stafford loans",
        "Have no outstanding balance as of Oct 1, 1998",
    ],
    "subjects_17500": [
        "Mathematics (secondary level)",
        "Science (secondary level)",
        "Special Education (any level)",
    ],
    "subjects_5000": [
        "Any subject at an elementary school",
        "Any subject at a secondary school in a shortage area",
    ],
    "how_to_apply": [
        "Complete the Teacher Loan Forgiveness Application",
        "Have your school's chief administrative officer certify your employment",
        "Submit to your loan servicer",
        "Check the TCLI directory: tcli.ed.gov to confirm your school qualifies",
    ],
    "pslf_note": (
        "You CANNOT count the same 5 years toward both Teacher Loan Forgiveness "
        "AND PSLF. If you plan to pursue PSLF (10 years), skip Teacher Forgiveness "
        "and let PSLF forgive the full balance — usually a better deal for high balances."
    ),
}

# ── For-profit school discharge programs ─────────────────────────────────────

DISCHARGE_PROGRAMS = {
    "borrower_defense": {
        "name": "Borrower Defense to Repayment",
        "law": "34 C.F.R. § 685.206(c)",
        "summary": (
            "If your school misled you — made false claims about job placement rates, "
            "accreditation, transfer credits, or earnings — you can apply for full "
            "loan discharge. The school lied to get your enrollment and loan dollars."
        ),
        "qualifying_claims": [
            "School made false or misleading statements about job placement rates",
            "School misrepresented accreditation status",
            "School claimed credits would transfer (and they didn't)",
            "School falsely represented salary outcomes or employment prospects",
            "School engaged in aggressive/deceptive recruiting practices",
        ],
        "how_to_apply": [
            "Apply at studentaid.gov/borrower-defense — completely free, no attorney needed",
            "Describe specifically what the school told you that turned out to be false",
            "Gather evidence: enrollment agreement, brochures, emails, written promises",
            "Your loans are placed in forbearance while the application is reviewed",
            "If approved: full discharge of loans from that school + refund of amounts paid",
        ],
        "status_note": (
            "The Borrower Defense program has been expanded and contracted multiple times "
            "under different administrations. As of 2026, check studentaid.gov for current "
            "processing status and timelines."
        ),
    },
    "closed_school": {
        "name": "Closed School Discharge",
        "law": "34 C.F.R. § 685.214",
        "summary": (
            "If your school closed while you were enrolled, or within 180 days of you "
            "withdrawing, you may be eligible for 100% discharge of your federal loans."
        ),
        "qualifying_conditions": [
            "School closed while you were enrolled",
            "School closed within 180 days of your withdrawal",
            "You did NOT complete the program via a teach-out agreement",
            "You have Direct Loans, FFEL loans, or Perkins loans from that school",
        ],
        "how_to_apply": [
            "Contact your loan servicer and request a Closed School Discharge application",
            "Or apply at studentaid.gov",
            "Your loans will be placed in forbearance during review",
        ],
    },
    "false_certification": {
        "name": "False Certification Discharge",
        "summary": (
            "If the school falsely certified your eligibility for federal aid — "
            "for example, you didn't have a high school diploma or GED but they "
            "certified you anyway — you may qualify for discharge."
        ),
        "qualifying_conditions": [
            "School certified you for aid when you didn't meet eligibility requirements",
            "School certified you despite a disqualifying status (criminal record, etc.)",
            "Your identity was used without your permission (identity theft)",
        ],
    },
}

# ── Known for-profit schools with discharge activity ─────────────────────────

KNOWN_SCHOOLS = {
    "itt tech": {
        "full_name": "ITT Technical Institute",
        "status": "CLOSED 2016",
        "discharge": "Closed School Discharge + Borrower Defense",
        "notes": (
            "ITT closed in September 2016. Former students qualify for Closed School "
            "Discharge. Additionally, the ED approved automatic Borrower Defense "
            "discharges for many ITT borrowers. Check studentaid.gov — you may "
            "already qualify for automatic relief without applying."
        ),
        "action": "Apply for Closed School Discharge at studentaid.gov immediately.",
    },
    "corinthian": {
        "full_name": "Corinthian Colleges (Everest, Heald, WyoTech)",
        "status": "CLOSED 2015",
        "discharge": "Borrower Defense — Sweet v. Cardona settlement",
        "notes": (
            "Corinthian students are covered by the Sweet v. Cardona class action "
            "settlement (2023). If you attended a Corinthian school, you qualify "
            "for automatic full discharge. No application needed if you're in the class."
        ),
        "action": "Check studentaid.gov/borrower-defense for your automatic discharge status.",
    },
    "full sail": {
        "full_name": "Full Sail University",
        "status": "OPEN — under scrutiny",
        "discharge": "Borrower Defense (case-by-case)",
        "notes": (
            "Full Sail has faced scrutiny over job placement rate claims and graduate "
            "outcomes in creative fields. Not automatically dischargeable, but Borrower "
            "Defense claims based on misrepresentation of employment outcomes have been "
            "filed and approved. You must document what specific claims the school made."
        ),
        "action": "File a Borrower Defense claim if the school made specific false claims. Document everything.",
    },
    "devry": {
        "full_name": "DeVry University",
        "status": "OPEN — FTC settlement 2016",
        "discharge": "Borrower Defense (case-by-case)",
        "notes": (
            "DeVry settled with the FTC in 2016 for $100M over misleading job "
            "placement rate claims. Borrower Defense claims citing these "
            "misrepresentations have been approved. File if you were told "
            "specific false statistics about employment."
        ),
        "action": "File Borrower Defense citing DeVry's FTC-proven false 90% job placement claims.",
    },
    "kaplan": {
        "full_name": "Kaplan University (now Purdue Global)",
        "status": "Sold to Purdue 2018",
        "discharge": "Borrower Defense (case-by-case)",
        "notes": (
            "Kaplan had documented issues with misrepresentation. Now operates as "
            "Purdue Global. Borrower Defense claims from Kaplan-era enrollment "
            "may still be filed."
        ),
        "action": "File Borrower Defense if you attended Kaplan before the Purdue acquisition and were misled.",
    },
    "art institute": {
        "full_name": "The Art Institutes (EDMC)",
        "status": "Mostly CLOSED 2018-2023",
        "discharge": "Closed School Discharge + Borrower Defense",
        "notes": (
            "Most Art Institute campuses closed between 2018-2023. EDMC (parent company) "
            "settled with multiple states for deceptive practices. Borrower Defense "
            "claims citing misrepresentation of job placement rates are eligible."
        ),
        "action": "Apply for Closed School Discharge if your campus closed. File Borrower Defense for misrepresentation.",
    },
}


def check_school(school_name: str) -> dict:
    """Check if a school has known discharge programs."""
    name_lower = school_name.lower()
    for key, data in KNOWN_SCHOOLS.items():
        if key in name_lower or name_lower in data["full_name"].lower():
            return data
    return {}


def pslf_status(years_worked: int, employer_type: str = "nonprofit") -> dict:
    """PSLF progress check."""
    payments_made = years_worked * 12
    payments_remaining = max(0, 120 - payments_made)
    years_remaining = payments_remaining // 12
    months_remaining = payments_remaining % 12

    qualifying = any(q.lower() in employer_type.lower() for q in [
        "government", "nonprofit", "501", "school", "hospital", "public", "military", "peace corps", "americorps"
    ])

    return {
        "payments_made": payments_made,
        "payments_remaining": payments_remaining,
        "years_remaining": years_remaining,
        "months_remaining": months_remaining,
        "likely_qualifying": qualifying,
        "formatted": (
            f"PSLF Progress Check\n"
            f"  Years worked:      {years_worked}\n"
            f"  Qualifying pmts:   {payments_made}/120\n"
            f"  Remaining:         {payments_remaining} payments "
            f"({years_remaining} yr {months_remaining} mo)\n"
            f"  Employer type:     {employer_type}\n"
            f"  Likely qualifying: {'YES' if qualifying else 'VERIFY — may not qualify'}\n"
            f"\n  CRITICAL: Submit your Employment Certification Form (ECF) NOW\n"
            f"  if you haven't done it this year. studentaid.gov/pslf\n"
        ),
    }


def compare_idr_plans(annual_income: float, family_size: int, balance: float) -> str:
    """Side-by-side comparison of all IDR plans."""
    lines = [
        f"IDR Plan Comparison",
        f"  Income: ${annual_income:,.0f}/yr | Family: {family_size} | Balance: ${balance:,.0f}",
        f"  {'Plan':<8} {'Monthly Pmt':>12} {'Annual':>10} {'Forgiveness':>12}",
        f"  {'─'*8} {'─'*12} {'─'*10} {'─'*12}",
    ]
    for plan_key, plan_data in IDR_PLANS.items():
        r = idr_payment(annual_income, family_size, plan_key)
        lines.append(
            f"  {plan_key:<8} ${r['monthly_payment']:>10,.2f} "
            f"${r['annual_payment']:>9,.2f} "
            f"{r['forgiveness_years']:>9} yrs"
        )
    lines += [
        f"",
        f"  Best for PSLF:  IBR (most legally stable) or SAVE (lowest payments)",
        f"  Parent PLUS:    Must consolidate first, then ICR is only option",
        f"  Enroll at:      studentaid.gov/manage-loans/repayment",
    ]
    return "\n".join(lines)


def analyze_situation(situation_text: str) -> str:
    """Parse a free-text student loan situation and return relevant guidance."""
    text = situation_text.lower()
    sections = []

    # Check for school name
    for key, data in KNOWN_SCHOOLS.items():
        if key in text:
            sections.append(
                f"── SCHOOL: {data['full_name']} ──────────────────\n"
                f"Status: {data['status']}\n"
                f"Discharge available: {data['discharge']}\n"
                f"{data['notes']}\n"
                f"ACTION: {data['action']}"
            )

    # PSLF
    if any(w in text for w in ["pslf", "public service", "nonprofit", "government job", "teacher", "nurse", "social worker"]):
        sections.append(
            f"── PUBLIC SERVICE LOAN FORGIVENESS ──────────────\n"
            f"Citation: {PSLF['law']}\n"
            f"{PSLF['summary']}\n\n"
            f"Critical steps:\n" +
            "\n".join(f"  {i+1}. {s}" for i, s in enumerate(PSLF["steps"])) +
            f"\n\nCommon mistakes:\n" +
            "\n".join(f"  • {m}" for m in PSLF["common_mistakes"])
        )

    # IDR
    if any(w in text for w in ["income", "payment too high", "can't afford", "idr", "income-driven", "save plan", "ibr"]):
        sections.append(
            f"── INCOME-DRIVEN REPAYMENT ──────────────────────\n"
            "Your payment can be reduced to as low as $0/mo based on your income.\n"
            "Enroll at studentaid.gov/manage-loans/repayment\n\n"
            "Best plans:\n"
            "  • SAVE: lowest payments for most borrowers (check current legal status)\n"
            "  • IBR: most legally stable, good for PSLF\n"
            "  • ICR: only option for consolidated Parent PLUS loans"
        )

    # Borrower Defense
    if any(w in text for w in ["borrower defense", "lied", "mislead", "misleading", "false", "discharge", "closed", "for-profit"]):
        prog = DISCHARGE_PROGRAMS["borrower_defense"]
        sections.append(
            f"── BORROWER DEFENSE TO REPAYMENT ────────────────\n"
            f"Citation: {prog['law']}\n"
            f"{prog['summary']}\n\n"
            f"How to apply:\n" +
            "\n".join(f"  {i+1}. {s}" for i, s in enumerate(prog["how_to_apply"]))
        )

    # Teacher
    if any(w in text for w in ["teacher", "teaching", "teach", "classroom", "title i"]):
        tf = TEACHER_FORGIVENESS
        sections.append(
            f"── TEACHER LOAN FORGIVENESS ─────────────────────\n"
            f"Amount: {tf['max_amount']}\n"
            f"Requirements: 5 years full-time at a Title I school\n"
            f"Check school eligibility: tcli.ed.gov\n\n"
            f"NOTE: {tf['pslf_note']}"
        )

    if not sections:
        sections.append(
            "── STUDENT LOAN GENERAL GUIDANCE ────────────────\n"
            "Key options to explore:\n"
            "  1. Are your loans federal or private? (studentaid.gov to check)\n"
            "  2. Are you on an IDR plan? If not, you may be overpaying.\n"
            "  3. Do you work for a government or nonprofit? PSLF may apply.\n"
            "  4. Did you attend a for-profit school? Discharge may be available.\n"
            "  5. Can't pay at all? Request forbearance or deferment to buy time.\n\n"
            "Start at: studentaid.gov — your complete loan picture is there."
        )

    return "\n\n".join(sections)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0].lower()

    if cmd == "pslf":
        years = int(args[args.index("--years") + 1]) if "--years" in args else 0
        employer = args[args.index("--employer") + 1] if "--employer" in args else "nonprofit"
        r = pslf_status(years, employer)
        print(r["formatted"])
        print("\nFull PSLF requirements:")
        for req in PSLF["requirements"]:
            print(f"  • {req}")

    elif cmd == "idr":
        income = float(args[args.index("--income") + 1]) if "--income" in args else 0
        family = int(args[args.index("--family") + 1]) if "--family" in args else 1
        balance = float(args[args.index("--balance") + 1]) if "--balance" in args else 0
        print(compare_idr_plans(income, family, balance))

    elif cmd == "school":
        name = args[args.index("--name") + 1] if "--name" in args else " ".join(args[1:])
        data = check_school(name)
        if data:
            print(f"\n{data['full_name']}")
            print(f"Status: {data['status']}")
            print(f"Discharge: {data['discharge']}")
            print(f"\n{data['notes']}")
            print(f"\nACTION: {data['action']}")
        else:
            print(f"\n'{name}' not in Nia's known school database.")
            print("This doesn't mean no discharge is available — search 'borrower defense [school name]'")
            print("or check studentaid.gov/borrower-defense")

    elif cmd == "forgiveness":
        ftype = args[args.index("--type") + 1] if "--type" in args else "pslf"
        if ftype == "teacher":
            tf = TEACHER_FORGIVENESS
            print(f"\n{tf['name']}")
            print(f"Amount: {tf['max_amount']}")
            print(f"\nRequirements:")
            for r in tf["requirements"]:
                print(f"  • {r}")
            print(f"\nSteps:")
            for i, s in enumerate(tf["how_to_apply"], 1):
                print(f"  {i}. {s}")
            print(f"\nNOTE: {tf['pslf_note']}")
        elif ftype == "borrower-defense":
            bd = DISCHARGE_PROGRAMS["borrower_defense"]
            print(f"\n{bd['name']}")
            print(f"Law: {bd['law']}")
            print(f"\n{bd['summary']}")
            print(f"\nSteps:")
            for i, s in enumerate(bd["how_to_apply"], 1):
                print(f"  {i}. {s}")

    elif cmd == "analyze":
        situation = " ".join(args[1:])
        if not situation:
            situation = input("Describe your student loan situation: ")
        print(analyze_situation(situation))

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: pslf, idr, school, forgiveness, analyze")
        sys.exit(1)


if __name__ == "__main__":
    main()
