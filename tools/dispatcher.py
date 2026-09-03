"""
Tool Dispatcher — Nia's automatic tool router.

Reads a Situation and runs the right tools based on what the person said.
Returns a structured findings dict that gets injected into agent context
before the model speaks — so agents always have verified data, never guess.

The dispatcher is intentionally simple:
  situation in → tool results out → agents speak from facts

No LLM involvement in tool selection — pure keyword matching + tool execution.
Fast, deterministic, impossible to hallucinate.
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.nia.intake import Situation


# ── Keyword triggers for each tool ───────────────────────────────────────────

CREDIT_KEYWORDS = {
    "charge-off", "charge off", "chargeoff", "collection", "collector",
    "credit report", "dispute", "experian", "equifax", "transunion",
    "credit score", "derogatory", "delinquent", "creditor", "fcra",
    "fdcpa", "credit bureau", "late payment", "judgment", "garnish",
    "chexsystems", "lexisnexis", "innovis", "nctue", "early warning",
    "debt validation", "cease and desist", "pay for delete",
}

STUDENT_LOAN_KEYWORDS = {
    "student loan", "fafsa", "pslf", "public service", "income driven",
    "income-driven", "idr", "save plan", "ibr", "paye", "borrower defense",
    "loan forgiveness", "teacher forgiveness", "itt tech", "itt technical",
    "corinthian", "full sail", "devry", "kaplan", "art institute",
    "for-profit school", "for profit school", "closed school",
    "loan discharge", "servicer", "navient", "nelnet", "aidvantage",
    "sallie mae", "federal loan",
}

HOUSE_HACK_KEYWORDS = {
    "house hack", "duplex", "triplex", "fourplex", "multi-unit", "multiunit",
    "multi unit", "fha loan", "buy a house", "first time buyer", "down payment",
    "brrrr", "real estate", "investment property", "rental property",
    "mortgage", "refinance", "landlord", "cash flow", "rental income",
}

BUSINESS_KEYWORDS = {
    "buy a business", "acquire a business", "business acquisition", "laundromat",
    "car wash", "vending", "small business", "sba loan", "sba 7a",
    "seller financing", "bizbuysell", "boring business", "cash flow business",
    "buy an existing", "owner financing", "letter of intent",
}

DEBT_CALC_KEYWORDS = {
    "pay off debt", "debt payoff", "credit card debt", "avalanche", "snowball",
    "interest rate", "minimum payment", "how long to pay", "how much interest",
    "high interest", "debt free",
}

SAVINGS_KEYWORDS = {
    "savings", "emergency fund", "high yield", "hysa", "cd ladder",
    "certificate of deposit", "i-bond", "share certificate", "save money",
    "reach my goal", "savings goal",
}

CFPB_KEYWORDS = {
    "complaint", "cfpb", "consumer financial", "file a complaint",
    "report a company", "collector calling", "harassment",
}


def _match(text: str, keywords: set) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def _extract_state(situation) -> str | None:
    return getattr(situation, "state", None)


# ── Individual tool runners ───────────────────────────────────────────────────

def _run_credit_law(situation) -> str | None:
    try:
        from tools.credit_law import format_analysis
        return format_analysis(situation.summary)
    except Exception as e:
        return f"[credit_law error: {e}]"


def _run_student_loans(situation) -> str | None:
    try:
        from tools.student_loans import analyze_situation
        return analyze_situation(situation.summary)
    except Exception as e:
        return f"[student_loans error: {e}]"


def _run_house_hack(situation) -> str | None:
    try:
        from tools.calculator import house_hack
        # Extract numbers if present, else return guidance
        text = situation.summary
        price_match = re.search(r'\$?([\d,]+)k?\s*(home|house|property|price|listing)', text, re.I)
        rent_match = re.search(r'\$?([\d,]+)\s*/?\s*(mo|month|monthly|rent)', text, re.I)

        if price_match and rent_match:
            price = float(price_match.group(1).replace(",", ""))
            if "k" in price_match.group(0).lower():
                price *= 1000
            rent = float(rent_match.group(1).replace(",", ""))
            r = house_hack(price, rent)
            return r["formatted"]
        else:
            return (
                "House Hack Guidance\n"
                "  Strategy: Buy a 2-4 unit property, live in one unit,\n"
                "  rent the others — tenants pay your mortgage.\n\n"
                "  Financing options:\n"
                "    • FHA loan: 3.5% down (min 580 credit score)\n"
                "    • VA loan: 0% down (if you're a veteran)\n"
                "    • Conventional: 5-20% down\n\n"
                "  2-4 units = residential financing (easier to qualify)\n"
                "  5+ units = commercial financing (harder)\n\n"
                "  Tell Nia the property price and expected rent\n"
                "  and she'll run the exact numbers for you."
            )
    except Exception as e:
        return f"[calculator error: {e}]"


def _run_business_calc(situation) -> str | None:
    try:
        from tools.calculator import business_acquisition
        text = situation.summary
        rev_match = re.search(r'\$?([\d,]+)k?\s*(revenue|annual|yearly|gross)', text, re.I)
        price_match = re.search(r'\$?([\d,]+)k?\s*(asking|price|listed|listing|cost)', text, re.I)

        if rev_match and price_match:
            revenue = float(rev_match.group(1).replace(",", ""))
            price = float(price_match.group(1).replace(",", ""))
            if "k" in rev_match.group(0).lower():
                revenue *= 1000
            if "k" in price_match.group(0).lower():
                price *= 1000
            expenses = revenue * 0.6  # rough 40% margin estimate
            r = business_acquisition(revenue, expenses, price)
            return r["formatted"]
        else:
            return (
                "Small Business Acquisition Guidance\n"
                "  The Codie Sanchez model: buy boring, cash-flowing businesses.\n\n"
                "  Best targets:\n"
                "    • Laundromats, car washes, storage facilities\n"
                "    • Landscaping, HVAC, plumbing routes\n"
                "    • Vending routes, ATM routes\n\n"
                "  Financing:\n"
                "    • SBA 7a loan: as little as 10% down\n"
                "    • Seller financing: owner carries the note\n"
                "    • Combination: SBA + seller note\n\n"
                "  Fair price: 2-3x annual SDE (seller's discretionary earnings)\n"
                "  Find deals: BizBuySell, Flippa, local brokers, cold outreach\n\n"
                "  Give Nia the revenue and asking price and she'll tell you\n"
                "  if it's a fair deal and what your monthly net would be."
            )
    except Exception as e:
        return f"[calculator error: {e}]"


def _run_debt_calc(situation) -> str | None:
    try:
        from tools.calculator import debt_payoff
        text = situation.summary
        balance_match = re.search(r'\$?([\d,]+)\s*(balance|debt|owe|credit card)', text, re.I)
        rate_match = re.search(r'([\d.]+)\s*%', text, re.I)
        payment_match = re.search(r'\$?([\d,]+)\s*/?\s*(mo|month|monthly|pay)', text, re.I)

        if balance_match and rate_match and payment_match:
            balance = float(balance_match.group(1).replace(",", ""))
            rate = float(rate_match.group(1))
            payment = float(payment_match.group(1).replace(",", ""))
            r = debt_payoff(balance, rate, payment)
            return r.get("formatted") or r.get("message")
        return None  # not enough numbers to calculate — skip
    except Exception:
        return None


def _run_cfpb_search(situation) -> str | None:
    try:
        from tools.web_search import search_cfpb_complaints, format_results
        # Extract company name — look for quoted names or known collector patterns
        text = situation.summary
        company_match = re.search(r'"([^"]+)"|([\w\s]+(?:collection|credit|financial|bank|capital)[s\s]*)', text, re.I)
        if company_match:
            company = (company_match.group(1) or company_match.group(2)).strip()
            results = search_cfpb_complaints(company)
            if results:
                return format_results(results, f"CFPB complaints: {company}")
        return None
    except Exception:
        return None


def _run_savings_calc(situation) -> str | None:
    try:
        from tools.calculator import savings_goal
        text = situation.summary
        goal_match = re.search(r'\$?([\d,]+)\s*(goal|save|savings|emergency fund|fund)', text, re.I)
        monthly_match = re.search(r'\$?([\d,]+)\s*/?\s*(mo|month|monthly|a month|per month)', text, re.I)

        if goal_match and monthly_match:
            goal = float(goal_match.group(1).replace(",", ""))
            monthly = float(monthly_match.group(1).replace(",", ""))
            r = savings_goal(goal, monthly)
            return r["formatted"]
        return None
    except Exception:
        return None


# ── Main dispatcher ───────────────────────────────────────────────────────────

def dispatch(situation) -> dict:
    """
    Given a Situation, run all relevant tools and return their findings.

    Returns:
        {
            "credit_law": "...",
            "student_loans": "...",
            "calculator": "...",
            "web_search": "...",
            ...
        }
        Only includes keys where tools produced output.
    """
    text = situation.summary + " " + situation.raw_input
    findings = {}

    # Credit law
    if _match(text, CREDIT_KEYWORDS):
        result = _run_credit_law(situation)
        if result:
            findings["credit_law"] = result

    # Student loans
    if _match(text, STUDENT_LOAN_KEYWORDS):
        result = _run_student_loans(situation)
        if result:
            findings["student_loans"] = result

    # House hack
    if _match(text, HOUSE_HACK_KEYWORDS):
        result = _run_house_hack(situation)
        if result:
            findings["house_hack"] = result

    # Business acquisition
    if _match(text, BUSINESS_KEYWORDS):
        result = _run_business_calc(situation)
        if result:
            findings["business"] = result

    # Debt calculator (only if we have numbers)
    if _match(text, DEBT_CALC_KEYWORDS):
        result = _run_debt_calc(situation)
        if result:
            findings["debt_calc"] = result

    # Savings calculator
    if _match(text, SAVINGS_KEYWORDS):
        result = _run_savings_calc(situation)
        if result:
            findings["savings"] = result

    # CFPB search (only if collector/complaint mentioned)
    if _match(text, CFPB_KEYWORDS):
        result = _run_cfpb_search(situation)
        if result:
            findings["cfpb"] = result

    return findings


def format_findings(findings: dict) -> str:
    """Format all tool findings into a single verified facts block."""
    if not findings:
        return ""
    sections = []
    labels = {
        "credit_law": "CREDIT LAW ANALYSIS",
        "student_loans": "STUDENT LOAN GUIDANCE",
        "house_hack": "HOUSE HACK ANALYSIS",
        "business": "BUSINESS ACQUISITION ANALYSIS",
        "debt_calc": "DEBT PAYOFF CALCULATION",
        "savings": "SAVINGS CALCULATION",
        "cfpb": "CFPB COMPLAINT SEARCH",
    }
    for key, content in findings.items():
        label = labels.get(key, key.upper())
        sections.append(f"── {label} {'─' * max(0, 50 - len(label))}\n{content}")
    return "\n\n".join(sections)
