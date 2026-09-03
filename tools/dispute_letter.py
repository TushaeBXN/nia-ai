"""
Dispute Letter Generator — produces ready-to-send credit dispute letters.

Generates certified-mail-ready dispute letters for:
  - Bureau verification disputes (FCRA § 611)
  - Debt validation letters (FDCPA § 809)
  - Cease and desist letters (FDCPA § 805)
  - Time-barred / SOL expiration notices
  - Pay-for-delete request letters
  - Method of verification demand letters

Usage:
    python -m tools.dispute_letter verification --bureau experian
    python -m tools.dispute_letter validation --collector "ABC Collections"
    python -m tools.dispute_letter cease --collector "XYZ Debt Services"
    python -m tools.dispute_letter sol-expired --bureau equifax --creditor "Capital One"
    python -m tools.dispute_letter method-of-verification --bureau transunion
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.credit_law import BUREAUS


TODAY = date.today().strftime("%B %d, %Y")

BUREAU_ADDRESSES = {
    "experian":   "Experian\nP.O. Box 4500\nAllen, TX 75013",
    "equifax":    "Equifax Information Services LLC\nP.O. Box 740256\nAtlanta, GA 30374",
    "transunion": "TransUnion Consumer Solutions\nP.O. Box 2000\nChester, PA 19016",
}


def _header(sender_name: str = "[YOUR FULL NAME]",
            sender_address: str = "[YOUR ADDRESS]",
            sender_city: str = "[CITY, STATE ZIP]",
            sender_phone: str = "[YOUR PHONE]",
            sender_email: str = "[YOUR EMAIL]") -> str:
    return (
        f"{sender_name}\n"
        f"{sender_address}\n"
        f"{sender_city}\n"
        f"{sender_phone}\n"
        f"{sender_email}\n\n"
        f"{TODAY}\n\n"
    )


def _certified_note() -> str:
    return (
        "SENT VIA CERTIFIED MAIL — RETURN RECEIPT REQUESTED\n"
        "Tracking #: [YOUR TRACKING NUMBER]\n\n"
    )


# ── Letter templates ──────────────────────────────────────────────────────────

def verification_dispute(
    bureau: str = "experian",
    creditor: str = None,
    creditor_name: str = "[CREDITOR NAME]",
    account: str = None,
    account_number: str = "[ACCOUNT NUMBER, LAST 4 DIGITS ONLY]",
    dispute_reason: str = "This item is inaccurate and/or cannot be verified.",
) -> str:
    if creditor:
        creditor_name = creditor
    if account:
        account_number = account
    bureau_key = bureau.lower()
    address = BUREAU_ADDRESSES.get(bureau_key, "[BUREAU ADDRESS]")
    bureau_name = BUREAUS.get(bureau_key, {}).get("name", bureau.title())

    return f"""{_certified_note()}{_header()}
{bureau_name}
{address}

RE: FORMAL DISPUTE OF INACCURATE CREDIT INFORMATION
    Creditor: {creditor_name}
    Account: {account_number}

To Whom It May Concern:

I am writing to formally dispute an inaccurate item on my credit report pursuant to
my rights under the Fair Credit Reporting Act (FCRA), 15 U.S.C. § 1681i.

ITEM DISPUTED:
  Creditor/Furnisher: {creditor_name}
  Account Number: {account_number}
  Reason for Dispute: {dispute_reason}

Under 15 U.S.C. § 1681i, you are required to:
  1. Forward my dispute to the furnisher within 5 business days
  2. Complete a reasonable investigation within 30 days of receiving this letter
     (or 45 days if I provide additional information)
  3. Delete the item if the furnisher cannot provide documented verification
  4. Provide me with written notice of the results of your investigation

Under 15 U.S.C. § 1681i(a)(7), I also request the METHOD OF VERIFICATION used
if you choose to "verify" this item rather than delete it.

Enclosed:
  [ ] Copy of credit report with disputed item highlighted
  [ ] Copy of my government-issued photo ID
  [ ] Copy of proof of address (utility bill or bank statement)

I expect written confirmation of receipt and results within the legally required timeframe.
Failure to investigate and respond within 30 days is a violation of federal law.

Sincerely,

[YOUR SIGNATURE]
{_header().split(chr(10))[0]}

---
NOTE: Send via USPS Certified Mail with Return Receipt (green card). Keep the
tracking number and the green card when it returns — these are your legal proof
that the bureau received your dispute on a specific date.
"""


def debt_validation(
    collector_name: str = "[COLLECTION AGENCY NAME]",
    collector_address: str = "[COLLECTION AGENCY ADDRESS]",
    account_number: str = "[ACCOUNT NUMBER IF KNOWN]",
    original_creditor: str = "[ORIGINAL CREDITOR IF KNOWN]",
) -> str:
    return f"""{_certified_note()}{_header()}
{collector_name}
{collector_address}

RE: DEMAND FOR DEBT VALIDATION
    Re: Account {account_number} / Original Creditor: {original_creditor}

To Whom It May Concern:

I am writing in response to your recent contact regarding the above-referenced account.
Pursuant to my rights under the Fair Debt Collection Practices Act (FDCPA),
15 U.S.C. § 1692g, I hereby formally request VALIDATION of this debt.

YOU ARE HEREBY NOTIFIED that:

  1. I dispute the validity of this debt in its entirety.
  2. You must CEASE ALL COLLECTION ACTIVITY — including phone calls, letters,
     and credit reporting — until you provide me with complete validation.
  3. Any continued collection activity before providing validation is a violation
     of 15 U.S.C. § 1692g and may subject your company to statutory damages
     of up to $1,000 per violation, plus attorney fees.

To validate this debt, you must provide ALL of the following:
  a) Proof that your company is licensed to collect debts in my state
  b) The name and address of the original creditor
  c) The original account number
  d) A complete account history showing how the alleged balance was calculated
  e) Proof that your company owns this debt OR written authorization from the
     original creditor granting you the right to collect it
  f) A copy of the signed agreement creating this alleged debt

If you are reporting this account to any credit bureau, you must also immediately
notify them that this account is disputed, pursuant to 15 U.S.C. § 1692e(8).

DO NOT contact me by telephone. All future communication must be in writing only,
sent to the address listed above.

Sincerely,

[YOUR SIGNATURE]
{_header().split(chr(10))[0]}

---
NOTE: Send via USPS Certified Mail. Do NOT make any payment — not even $1 —
until you receive full validation. A payment can restart the Statute of Limitations.
"""


def cease_and_desist(
    collector_name: str = "[COLLECTION AGENCY NAME]",
    collector_address: str = "[COLLECTION AGENCY ADDRESS]",
    account_number: str = "[ACCOUNT NUMBER IF KNOWN]",
) -> str:
    return f"""{_certified_note()}{_header()}
{collector_name}
{collector_address}

RE: CEASE AND DESIST — ALL COLLECTION COMMUNICATIONS
    Re: Account {account_number}

To Whom It May Concern:

Pursuant to my rights under the Fair Debt Collection Practices Act (FDCPA),
15 U.S.C. § 1692c(c), I hereby demand that you IMMEDIATELY CEASE AND DESIST
all communication with me regarding the above-referenced account.

This includes:
  • All telephone calls to any number associated with me
  • All written correspondence to any address associated with me
  • All contact with any third parties regarding this alleged debt
  • All contact with my employer

You are legally permitted only ONE additional contact after receiving this letter:
to notify me that you are ceasing collection efforts, or to inform me of a specific
legal action (such as filing a lawsuit).

Any contact beyond that single permitted communication will constitute a willful
violation of 15 U.S.C. § 1692c, subjecting your company to:
  • Statutory damages up to $1,000 per violation
  • Actual damages
  • Attorney fees and court costs

I am retaining copies of all correspondence and documenting all contact attempts.

Sincerely,

[YOUR SIGNATURE]
{_header().split(chr(10))[0]}

---
NOTE: This letter stops calls and letters. It does NOT make the debt go away.
If they sue you, you must respond. Consult a consumer rights attorney — many
take FDCPA cases on contingency (no cost to you).
"""


def sol_expired(
    bureau: str = "experian",
    creditor_name: str = "[CREDITOR NAME]",
    account_number: str = "[ACCOUNT NUMBER]",
    dofd: str = "[DATE OF FIRST DELINQUENCY]",
    report_expiration: str = "[DATE 7 YEARS AFTER DOFD]",
) -> str:
    bureau_key = bureau.lower()
    address = BUREAU_ADDRESSES.get(bureau_key, "[BUREAU ADDRESS]")
    bureau_name = BUREAUS.get(bureau_key, {}).get("name", bureau.title())

    return f"""{_certified_note()}{_header()}
{bureau_name}
{address}

RE: DEMAND FOR DELETION — ITEM PAST FCRA REPORTING PERIOD
    Creditor: {creditor_name}
    Account: {account_number}

To Whom It May Concern:

I am writing to demand the immediate deletion of an item that has exceeded the
maximum reporting period permitted under the Fair Credit Reporting Act (FCRA),
15 U.S.C. § 1681c.

ITEM TO BE DELETED:
  Creditor/Furnisher: {creditor_name}
  Account Number: {account_number}
  Date of First Delinquency (DOFD): {dofd}
  FCRA 7-Year Reporting Limit Expired: {report_expiration}

Under 15 U.S.C. § 1681c(a), negative information may not appear on a consumer
credit report for more than 7 years from the Date of First Delinquency.

The Date of First Delinquency for this account is {dofd}. The 7-year reporting
period therefore expired on {report_expiration}. Continued reporting of this item
beyond that date is a VIOLATION of federal law.

I demand that you:
  1. Immediately delete this item from my credit report
  2. Notify all parties who received my credit report in the past 6 months
     of the deletion, pursuant to 15 U.S.C. § 1681i(d)
  3. Provide me with written confirmation of the deletion within 30 days

Continued reporting of this expired item may subject your company to civil
liability under 15 U.S.C. § 1681n and § 1681o.

Sincerely,

[YOUR SIGNATURE]
{_header().split(chr(10))[0]}
"""


def method_of_verification(
    bureau: str = "experian",
    creditor_name: str = "[CREDITOR NAME]",
    account_number: str = "[ACCOUNT NUMBER]",
    prior_dispute_date: str = "[DATE OF YOUR PRIOR DISPUTE]",
) -> str:
    bureau_key = bureau.lower()
    address = BUREAU_ADDRESSES.get(bureau_key, "[BUREAU ADDRESS]")
    bureau_name = BUREAUS.get(bureau_key, {}).get("name", bureau.title())

    return f"""{_certified_note()}{_header()}
{bureau_name}
{address}

RE: REQUEST FOR METHOD OF VERIFICATION
    Creditor: {creditor_name}
    Account: {account_number}
    Prior Dispute Submitted: {prior_dispute_date}

To Whom It May Concern:

On {prior_dispute_date}, I submitted a formal dispute regarding the above-referenced
account. You responded by stating that the item was "verified." I am now exercising
my right under 15 U.S.C. § 1681i(a)(7) to request a full description of the
procedure used to verify this item.

Specifically, I request:
  1. The name, address, and telephone number of the person at the furnisher who
     was contacted to verify this item
  2. The specific documents reviewed as part of the verification
  3. The specific data fields that were verified and by what means
  4. A copy of any documentation provided by the furnisher during verification

A checkbox response or a statement that the furnisher "confirmed" the information
is NOT sufficient verification under 15 U.S.C. § 1681i. The FCRA requires a
genuine, documented investigation — not a rubber stamp.

If you cannot provide this documentation within 15 days, I demand immediate
deletion of this item as unverifiable under 15 U.S.C. § 1681i(a)(5)(A).

Sincerely,

[YOUR SIGNATURE]
{_header().split(chr(10))[0]}
"""


def pay_for_delete(
    creditor_name: str = "[CREDITOR/COLLECTOR NAME]",
    creditor_address: str = "[CREDITOR ADDRESS]",
    account_number: str = "[ACCOUNT NUMBER]",
    offer_amount: str = "[AMOUNT YOU ARE OFFERING]",
    original_balance: str = "[ORIGINAL BALANCE]",
) -> str:
    return f"""{_certified_note()}{_header()}
{creditor_name}
{creditor_address}

RE: SETTLEMENT OFFER — PAY FOR DELETE
    Account: {account_number}
    Original Balance: {original_balance}

To Whom It May Concern:

I am writing regarding the above-referenced account currently reporting on my
credit report. I am prepared to resolve this account under the following conditions.

SETTLEMENT OFFER:
  I will pay {offer_amount} as settlement in full for the above account.

CONDITIONS (ALL must be met before any payment is made):
  1. You agree IN WRITING to request deletion of this tradeline from ALL three
     major credit bureaus (Experian, Equifax, TransUnion) within 30 days of payment
  2. You agree that this payment constitutes full and final settlement of the account
  3. You agree not to re-sell or transfer this account to any other collector
  4. You provide this agreement on company letterhead, signed by an authorized representative

I will NOT make any payment until I receive a signed written agreement satisfying
ALL conditions above. This offer expires 30 days from the date of this letter.

Upon receipt of the signed agreement, I will remit payment via [money order/cashier's check].

Please respond in writing only to the address listed above.

Sincerely,

[YOUR SIGNATURE]
{_header().split(chr(10))[0]}

---
NOTE: The major bureaus ended formal pay-for-delete agreements with large creditors
in 2022. This works best with smaller collection agencies and original creditors.
Get the agreement BEFORE you pay — once money changes hands, your leverage is gone.
"""


# ── CLI ───────────────────────────────────────────────────────────────────────

LETTER_MAP = {
    "verification":          verification_dispute,
    "validation":            debt_validation,
    "cease":                 cease_and_desist,
    "sol-expired":           sol_expired,
    "method-of-verification": method_of_verification,
    "pay-for-delete":        pay_for_delete,
}


def generate(letter_type: str, **kwargs) -> str:
    fn = LETTER_MAP.get(letter_type)
    if not fn:
        return f"Unknown letter type: {letter_type}\nOptions: {', '.join(LETTER_MAP)}"
    return fn(**{k: v for k, v in kwargs.items() if v})


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    letter_type = args[0]
    kwargs = {}
    i = 1
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            key = args[i][2:].replace("-", "_")
            kwargs[key] = args[i + 1]
            i += 2
        else:
            i += 1

    print(generate(letter_type, **kwargs))


if __name__ == "__main__":
    main()
