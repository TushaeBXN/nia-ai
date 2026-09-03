"""
Financial Calculator — Nia's numbers engine.

No hallucination possible here — pure math. Returns structured results
the agents can present verbatim.

Usage:
    python -m tools.calculator debt --balance 8500 --rate 24.99 --payment 250
    python -m tools.calculator payoff --balance 8500 --rate 24.99 --target 36
    python -m tools.calculator house-hack --price 280000 --rent 1800 --units 2
    python -m tools.calculator business --revenue 180000 --expenses 110000 --price 350000
    python -m tools.calculator mortgage --price 280000 --down 10 --rate 7.25 --years 30
    python -m tools.calculator avalanche --debts "Visa:4500:24.99,Discover:2100:19.99,Car:8000:6.9"
    python -m tools.calculator savings --goal 10000 --monthly 400 --rate 4.5
"""

import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── Core math ─────────────────────────────────────────────────────────────────

def monthly_payment(principal: float, annual_rate: float, months: int) -> float:
    """Standard amortization payment formula."""
    if annual_rate == 0:
        return principal / months
    r = annual_rate / 100 / 12
    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)


def months_to_payoff(principal: float, annual_rate: float, payment: float) -> int | None:
    """Months until balance reaches zero at a fixed payment. Returns None if payment < interest."""
    if annual_rate == 0:
        return math.ceil(principal / payment)
    r = annual_rate / 100 / 12
    interest_only = principal * r
    if payment <= interest_only:
        return None  # Never paid off
    months = -math.log(1 - (principal * r) / payment) / math.log(1 + r)
    return math.ceil(months)


def total_interest(principal: float, annual_rate: float, payment: float) -> float:
    """Total interest paid over the life of the loan."""
    n = months_to_payoff(principal, annual_rate, payment)
    if n is None:
        return float("inf")
    return payment * n - principal


# ── Calculators ───────────────────────────────────────────────────────────────

def debt_payoff(balance: float, rate: float, payment: float) -> dict:
    """
    How long to pay off a single debt at a fixed payment.
    """
    months = months_to_payoff(balance, rate, payment)
    interest_only = balance * (rate / 100 / 12)

    if months is None:
        return {
            "error": True,
            "message": (
                f"Your payment of ${payment:,.2f}/mo doesn't cover the monthly interest "
                f"of ${interest_only:,.2f}. The balance will GROW every month. "
                f"You need to pay at least ${math.ceil(interest_only) + 1:,.2f}/mo to make progress."
            ),
        }

    total_paid = payment * months
    total_interest_paid = total_paid - balance
    years = months // 12
    remaining_months = months % 12

    return {
        "balance": balance,
        "rate": rate,
        "payment": payment,
        "months_to_payoff": months,
        "years": years,
        "remaining_months": remaining_months,
        "total_paid": total_paid,
        "total_interest": total_interest_paid,
        "interest_pct_of_total": (total_interest_paid / total_paid) * 100,
        "formatted": (
            f"Debt Payoff Analysis\n"
            f"  Balance:        ${balance:>10,.2f}\n"
            f"  Interest rate:  {rate:.2f}% APR\n"
            f"  Monthly payment: ${payment:>9,.2f}\n"
            f"  ─────────────────────────────\n"
            f"  Paid off in:    {years} yr {remaining_months} mo ({months} months)\n"
            f"  Total paid:     ${total_paid:>10,.2f}\n"
            f"  Total interest: ${total_interest_paid:>10,.2f}  "
            f"({total_interest_paid/total_paid*100:.0f}% of what you pay goes to interest)\n"
        ),
    }


def required_payment(balance: float, rate: float, target_months: int) -> dict:
    """What monthly payment is needed to pay off a debt in X months?"""
    pmt = monthly_payment(balance, rate, target_months)
    total_paid = pmt * target_months
    total_interest_paid = total_paid - balance
    years = target_months // 12
    remaining_months = target_months % 12

    return {
        "balance": balance,
        "rate": rate,
        "target_months": target_months,
        "required_payment": pmt,
        "total_paid": total_paid,
        "total_interest": total_interest_paid,
        "formatted": (
            f"Required Payment to Pay Off in {years} yr {remaining_months} mo\n"
            f"  Balance:         ${balance:>10,.2f}\n"
            f"  Interest rate:   {rate:.2f}% APR\n"
            f"  Target timeline: {years} yr {remaining_months} mo\n"
            f"  ─────────────────────────────\n"
            f"  Required payment: ${pmt:>9,.2f}/mo\n"
            f"  Total paid:      ${total_paid:>10,.2f}\n"
            f"  Total interest:  ${total_interest_paid:>10,.2f}\n"
        ),
    }


def avalanche_payoff(debts: list[tuple[str, float, float]], extra: float = 0) -> dict:
    """
    Debt avalanche: pay minimums on all, throw extra at highest-rate debt first.
    debts: list of (name, balance, annual_rate)
    Returns payoff order, total interest, total months.
    """
    # Minimum payment = 1% of balance or $25, whichever is higher
    accounts = []
    for name, balance, rate in debts:
        min_pmt = max(round(balance * 0.01, 2), 25.0)
        accounts.append({
            "name": name,
            "balance": balance,
            "rate": rate,
            "min_payment": min_pmt,
        })

    # Sort highest rate first (avalanche)
    accounts.sort(key=lambda x: x["rate"], reverse=True)

    total_min = sum(a["min_payment"] for a in accounts)
    total_payment = total_min + extra

    # Simulate month by month
    month = 0
    total_interest_paid = 0
    payoff_order = []
    balances = {a["name"]: a["balance"] for a in accounts}

    while any(b > 0 for b in balances.values()):
        month += 1
        if month > 600:  # 50 year cap
            break

        remaining_payment = total_payment

        # Apply interest and minimums
        for acct in accounts:
            name = acct["name"]
            if balances[name] <= 0:
                continue
            interest = balances[name] * (acct["rate"] / 100 / 12)
            total_interest_paid += interest
            balances[name] += interest

        # Pay minimums on all non-focus debts first
        for acct in accounts[1:]:
            name = acct["name"]
            if balances[name] <= 0:
                continue
            pmt = min(acct["min_payment"], balances[name])
            balances[name] -= pmt
            remaining_payment -= pmt

        # Throw remaining at focus debt (highest rate)
        for acct in accounts:
            name = acct["name"]
            if balances[name] <= 0:
                continue
            pmt = min(remaining_payment, balances[name])
            balances[name] -= pmt
            remaining_payment -= pmt
            if balances[name] <= 0.01:
                balances[name] = 0
                payoff_order.append((name, month))
            break

        # Check all others paid off
        for acct in accounts[1:]:
            name = acct["name"]
            if balances[name] <= 0.01:
                balances[name] = 0
                if not any(p[0] == name for p in payoff_order):
                    payoff_order.append((name, month))

    years = month // 12
    remaining_months = month % 12
    total_paid = total_payment * month

    lines = [
        f"Debt Avalanche Plan  (highest-rate first)",
        f"  Monthly budget:  ${total_payment:>10,.2f}  (minimums ${total_min:,.2f} + extra ${extra:,.2f})",
        f"  ──────────────────────────────────────────",
    ]
    for name, mo in payoff_order:
        yr = mo // 12
        mo_r = mo % 12
        lines.append(f"  {name:<20} paid off in {yr} yr {mo_r} mo")
    lines += [
        f"  ──────────────────────────────────────────",
        f"  Debt-free in:    {years} yr {remaining_months} mo ({month} months)",
        f"  Total paid:      ${total_paid:>10,.2f}",
        f"  Total interest:  ${total_interest_paid:>10,.2f}",
    ]

    return {
        "months": month,
        "total_interest": total_interest_paid,
        "payoff_order": payoff_order,
        "formatted": "\n".join(lines),
    }


def house_hack(
    purchase_price: float,
    monthly_rent: float,       # rent from tenant unit(s)
    num_units: int = 2,
    down_pct: float = 3.5,     # FHA default
    rate: float = 7.25,
    loan_years: int = 30,
    monthly_expenses: float = None,  # taxes + insurance + maintenance estimate
) -> dict:
    """
    House hack analysis: buy multi-unit, live in one, rent the others.
    """
    down_payment = purchase_price * (down_pct / 100)
    loan_amount = purchase_price - down_payment

    # FHA MIP if < 20% down
    fha_mip_monthly = 0
    if down_pct < 20:
        fha_mip_monthly = loan_amount * 0.0055 / 12  # ~0.55% annual MIP

    pmt = monthly_payment(loan_amount, rate, loan_years * 12)
    total_monthly_pmt = pmt + fha_mip_monthly

    # Estimate expenses if not provided: 1.5% of purchase price annually
    if monthly_expenses is None:
        monthly_expenses = (purchase_price * 0.015) / 12

    total_monthly_cost = total_monthly_pmt + monthly_expenses
    net_monthly_cost = total_monthly_cost - monthly_rent
    annual_savings = monthly_rent * 12

    # Effective rent you pay vs renting
    cashflow_positive = net_monthly_cost <= 0

    lines = [
        f"House Hack Analysis — {num_units}-Unit Property",
        f"  Purchase price:   ${purchase_price:>10,.2f}",
        f"  Down payment:     ${down_payment:>10,.2f}  ({down_pct:.1f}%)",
        f"  Loan amount:      ${loan_amount:>10,.2f}",
        f"  Interest rate:    {rate:.2f}% / {loan_years} years",
        f"  ──────────────────────────────────────────",
        f"  Mortgage P&I:     ${pmt:>10,.2f}/mo",
    ]
    if fha_mip_monthly > 0:
        lines.append(f"  FHA MIP:          ${fha_mip_monthly:>10,.2f}/mo")
    lines += [
        f"  Est. expenses:    ${monthly_expenses:>10,.2f}/mo  (taxes, insurance, maintenance)",
        f"  Total cost:       ${total_monthly_cost:>10,.2f}/mo",
        f"  Tenant rent:     -${monthly_rent:>10,.2f}/mo",
        f"  ──────────────────────────────────────────",
        f"  YOUR NET COST:    ${net_monthly_cost:>10,.2f}/mo",
        f"",
    ]
    if cashflow_positive:
        lines.append(
            f"  CASH FLOW POSITIVE — tenants pay MORE than your total cost.\n"
            f"  You live FREE and collect ${abs(net_monthly_cost):,.2f}/mo profit."
        )
    else:
        avg_rent_1br = 1200  # rough national estimate
        lines.append(
            f"  You pay ${net_monthly_cost:,.2f}/mo to own a {num_units}-unit property\n"
            f"  vs. paying ~${avg_rent_1br:,.2f}/mo+ to rent nothing.\n"
            f"  You're building equity while tenants cover most of your cost."
        )
    lines += [
        f"",
        f"  Tenant covers:    ${annual_savings:,.2f}/yr of your housing cost",
        f"  5-yr equity est:  ${loan_amount * 0.04 * 5:,.2f}  (principal paydown alone)",
    ]

    return {
        "net_monthly_cost": net_monthly_cost,
        "cashflow_positive": cashflow_positive,
        "down_payment": down_payment,
        "monthly_payment": total_monthly_pmt,
        "formatted": "\n".join(lines),
    }


def mortgage(
    price: float,
    down_pct: float = 20.0,
    rate: float = 7.25,
    years: int = 30,
) -> dict:
    """Standard mortgage payment breakdown."""
    down = price * (down_pct / 100)
    loan = price - down
    pmt = monthly_payment(loan, rate, years * 12)
    total_paid = pmt * years * 12
    total_interest = total_paid - loan

    return {
        "down_payment": down,
        "loan_amount": loan,
        "monthly_payment": pmt,
        "total_paid": total_paid,
        "total_interest": total_interest,
        "formatted": (
            f"Mortgage Estimate\n"
            f"  Home price:      ${price:>10,.2f}\n"
            f"  Down payment:    ${down:>10,.2f}  ({down_pct:.1f}%)\n"
            f"  Loan amount:     ${loan:>10,.2f}\n"
            f"  Rate / Term:     {rate:.2f}% / {years} years\n"
            f"  ─────────────────────────────\n"
            f"  Monthly P&I:     ${pmt:>10,.2f}\n"
            f"  Total paid:      ${total_paid:>10,.2f}\n"
            f"  Total interest:  ${total_interest:>10,.2f}\n"
        ),
    }


def business_acquisition(
    annual_revenue: float,
    annual_expenses: float,
    asking_price: float,
    down_pct: float = 10.0,    # SBA 7a typical minimum
    loan_rate: float = 9.5,    # SBA current rate estimate
    loan_years: int = 10,
) -> dict:
    """
    Small business acquisition analysis (Codie Sanchez / boring business model).
    SDE = Seller's Discretionary Earnings = revenue - expenses (owner's real take-home).
    """
    sde = annual_revenue - annual_expenses
    sde_monthly = sde / 12
    valuation_multiple = asking_price / sde if sde > 0 else 0

    down_payment = asking_price * (down_pct / 100)
    loan_amount = asking_price - down_payment
    loan_pmt = monthly_payment(loan_amount, loan_rate, loan_years * 12)

    net_monthly = sde_monthly - loan_pmt
    annual_roi = (net_monthly * 12) / down_payment * 100 if down_payment > 0 else 0
    payback_years = down_payment / (net_monthly * 12) if net_monthly > 0 else None

    # Is this a fair price?
    if valuation_multiple < 2:
        price_verdict = "GREAT DEAL — under 2x SDE is rare and below market"
    elif valuation_multiple <= 3:
        price_verdict = "FAIR — 2-3x SDE is standard for small service businesses"
    elif valuation_multiple <= 4:
        price_verdict = "HIGH — negotiate down or look for a reason this premium is justified"
    else:
        price_verdict = "OVERPRICED — above 4x SDE for a small business needs major justification"

    lines = [
        f"Business Acquisition Analysis",
        f"  Annual revenue:   ${annual_revenue:>10,.2f}",
        f"  Annual expenses:  ${annual_expenses:>10,.2f}",
        f"  SDE (owner take): ${sde:>10,.2f}/yr  (${sde_monthly:,.2f}/mo)",
        f"  Asking price:     ${asking_price:>10,.2f}",
        f"  Price multiple:   {valuation_multiple:.1f}x SDE — {price_verdict}",
        f"  ──────────────────────────────────────────",
        f"  Down payment:     ${down_payment:>10,.2f}  ({down_pct:.0f}% — SBA 7a minimum)",
        f"  SBA loan:         ${loan_amount:>10,.2f}  @ {loan_rate:.1f}% / {loan_years} yr",
        f"  Loan payment:    -${loan_pmt:>10,.2f}/mo",
        f"  ──────────────────────────────────────────",
        f"  NET MONTHLY:      ${net_monthly:>10,.2f}/mo  (after debt service)",
        f"  Annual net:       ${net_monthly*12:>10,.2f}/yr",
        f"  ROI on down pmt:  {annual_roi:.1f}%/yr",
    ]
    if payback_years:
        lines.append(f"  Down pmt payback: {payback_years:.1f} years")
    if net_monthly < 0:
        lines.append(
            f"\n  ⚠ WARNING: Loan payments exceed SDE. This deal loses money at current price."
            f"\n  Negotiate asking price down to ${sde * 2.5:,.0f} (2.5x SDE) or walk."
        )

    return {
        "sde": sde,
        "net_monthly": net_monthly,
        "roi_pct": annual_roi,
        "valuation_multiple": valuation_multiple,
        "price_verdict": price_verdict,
        "formatted": "\n".join(lines),
    }


def savings_goal(goal: float, monthly_contribution: float, annual_rate: float = 4.5) -> dict:
    """How long to reach a savings goal with compound interest."""
    r = annual_rate / 100 / 12
    if r == 0:
        months = math.ceil(goal / monthly_contribution)
    else:
        # Future value of annuity: solve for n
        # goal = pmt * ((1+r)^n - 1) / r
        months = math.ceil(
            math.log(1 + (goal * r) / monthly_contribution) / math.log(1 + r)
        )

    years = months // 12
    remaining_months = months % 12
    total_contributed = monthly_contribution * months
    interest_earned = goal - total_contributed if goal > total_contributed else 0

    # If they save more than the goal via contributions alone
    if total_contributed >= goal:
        actual_months = math.ceil(goal / monthly_contribution)
        years = actual_months // 12
        remaining_months = actual_months % 12

    return {
        "goal": goal,
        "monthly_contribution": monthly_contribution,
        "rate": annual_rate,
        "months": months,
        "formatted": (
            f"Savings Goal Analysis\n"
            f"  Goal:             ${goal:>10,.2f}\n"
            f"  Monthly savings:  ${monthly_contribution:>10,.2f}\n"
            f"  APY (HYSA/CD):    {annual_rate:.2f}%\n"
            f"  ─────────────────────────────\n"
            f"  Reach goal in:   {years} yr {remaining_months} mo\n"
            f"  Total deposited: ${total_contributed:>10,.2f}\n"
            f"  Interest earned: ${interest_earned:>10,.2f}  (free money)\n"
        ),
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def _arg(args: list, flag: str, default=None):
    """Extract --flag value from args list."""
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    return default


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0].lower()

    if cmd == "debt":
        balance = float(_arg(args, "--balance", 0))
        rate = float(_arg(args, "--rate", 0))
        payment = float(_arg(args, "--payment", 0))
        r = debt_payoff(balance, rate, payment)
        print(r.get("formatted") or r.get("message"))

    elif cmd == "payoff":
        balance = float(_arg(args, "--balance", 0))
        rate = float(_arg(args, "--rate", 0))
        target = int(_arg(args, "--target", 36))
        r = required_payment(balance, rate, target)
        print(r["formatted"])

    elif cmd == "avalanche":
        raw = _arg(args, "--debts", "")
        extra = float(_arg(args, "--extra", 0))
        debts = []
        for item in raw.split(","):
            parts = item.strip().split(":")
            if len(parts) == 3:
                debts.append((parts[0], float(parts[1]), float(parts[2])))
        r = avalanche_payoff(debts, extra)
        print(r["formatted"])

    elif cmd == "house-hack":
        price = float(_arg(args, "--price", 0))
        rent = float(_arg(args, "--rent", 0))
        units = int(_arg(args, "--units", 2))
        down = float(_arg(args, "--down", 3.5))
        rate = float(_arg(args, "--rate", 7.25))
        r = house_hack(price, rent, units, down, rate)
        print(r["formatted"])

    elif cmd == "mortgage":
        price = float(_arg(args, "--price", 0))
        down = float(_arg(args, "--down", 20))
        rate = float(_arg(args, "--rate", 7.25))
        years = int(_arg(args, "--years", 30))
        r = mortgage(price, down, rate, years)
        print(r["formatted"])

    elif cmd == "business":
        revenue = float(_arg(args, "--revenue", 0))
        expenses = float(_arg(args, "--expenses", 0))
        price = float(_arg(args, "--price", 0))
        down = float(_arg(args, "--down", 10))
        r = business_acquisition(revenue, expenses, price, down)
        print(r["formatted"])

    elif cmd == "savings":
        goal = float(_arg(args, "--goal", 0))
        monthly = float(_arg(args, "--monthly", 0))
        rate = float(_arg(args, "--rate", 4.5))
        r = savings_goal(goal, monthly, rate)
        print(r["formatted"])

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: debt, payoff, avalanche, house-hack, mortgage, business, savings")
        sys.exit(1)


if __name__ == "__main__":
    main()
