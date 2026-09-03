"""
David — Legal Navigator
Matches situations to potential legal hooks and builds the documentation
foundation an attorney can act on. Not a lawyer; never pretends to be.
"""

from agents.common import speak
from agents.nia.intake import Domain

# Domain → potential legal hooks. Plain language, verified names and
# deadlines only. LEGAL REVIEW REQUIRED before deployment (see STATUS.md).
# Also consumed by tools/document_generator.py.
LEGAL_HOOKS = {
    Domain.HOUSING: [
        {
            "law": "Fair Housing Act",
            "covers": "Discrimination in renting, buying, or lending because of "
                      "race, color, religion, national origin, sex, disability, "
                      "or having children. Retaliation for complaining is also illegal.",
            "agency": "HUD Office of Fair Housing — 1-800-669-9777, hud.gov/fairhousing",
            "deadline": "1 YEAR to file with HUD; 2 years for a federal lawsuit",
        },
        {
            "law": "Section 1981 (Civil Rights Act of 1866)",
            "covers": "Race discrimination in any contract — including leases. "
                      "Applies even where the Fair Housing Act might not.",
            "agency": "Requires a private attorney (many take these free on contingency)",
            "deadline": "Generally 4 years",
        },
    ],
    Domain.EMPLOYMENT: [
        {
            "law": "Title VII (Civil Rights Act of 1964)",
            "covers": "Workplace discrimination because of race, color, religion, "
                      "sex, or national origin — hiring, pay, promotion, firing. "
                      "Retaliation for reporting it is separately illegal, even if "
                      "the original complaint isn't proven.",
            "agency": "EEOC — 1-800-669-4000, eeoc.gov (file online, by phone, or in person)",
            "deadline": "180 DAYS from the incident (300 in states with their own agency) — do not wait",
        },
        {
            "law": "Equal Pay Act",
            "covers": "Being paid less than someone of a different sex for "
                      "substantially equal work.",
            "agency": "EEOC — 1-800-669-4000",
            "deadline": "2 years (3 if the violation was willful)",
        },
        {
            "law": "Fair Labor Standards Act (wage theft)",
            "covers": "Unpaid wages, unpaid overtime, minimum wage violations.",
            "agency": "U.S. Dept. of Labor Wage & Hour Division — 1-866-487-9243",
            "deadline": "2 years (3 if willful)",
        },
    ],
    Domain.HEALTHCARE: [
        {
            "law": "Section 1557 (Affordable Care Act)",
            "covers": "Discrimination by hospitals, clinics, doctors, and insurers "
                      "that receive federal money (almost all do) — including being "
                      "dismissed, denied care, or treated worse because of race.",
            "agency": "HHS Office for Civil Rights — 1-800-368-1019, hhs.gov/ocr",
            "deadline": "180 DAYS from the incident",
        },
        {
            "law": "EMTALA",
            "covers": "Any ER that takes Medicare (almost all) MUST screen and "
                      "stabilize you in an emergency — including active labor — "
                      "regardless of ability to pay, insurance, or status.",
            "agency": "Report violations to CMS via your state health department, "
                      "and to the hospital's patient advocate",
            "deadline": "Report as soon as possible; civil suits generally 2 years",
        },
    ],
    Domain.EDUCATION: [
        {
            "law": "Title VI (Civil Rights Act of 1964)",
            "covers": "Race or national-origin discrimination by any school that "
                      "receives federal funds — discipline disparities, denial of "
                      "programs, hostile environment the school ignores.",
            "agency": "U.S. Dept. of Education Office for Civil Rights — "
                      "1-800-421-3481, ocrcas.ed.gov",
            "deadline": "180 DAYS from the incident",
        },
        {
            "law": "State open-meeting and curriculum laws",
            "covers": "School boards must follow public process to change curricula. "
                      "What a district *says* a state law requires is often broader "
                      "than what the law actually says — get the actual bill text.",
            "agency": "State ACLU affiliate; local school board public comment",
            "deadline": "Varies — school board procedures move fast",
        },
    ],
    Domain.IMMIGRATION: [
        {
            "law": "U.S. Constitution (4th & 5th Amendments)",
            "covers": "EVERYONE in the U.S., regardless of status: the right to "
                      "remain silent, to refuse entry without a judge-signed warrant, "
                      "and to talk to a lawyer before signing anything.",
            "agency": "Immigration attorney immediately — never sign anything first",
            "deadline": "Rights apply at all times; act immediately on detention",
        },
        {
            "law": "Right to a hearing",
            "covers": "Most people have the right to see an immigration judge "
                      "before removal. Do not sign a 'voluntary departure' or "
                      "'stipulated removal' without a lawyer.",
            "agency": "EOIR automated case line — 1-800-898-7180 | "
                      "Find someone detained: locator.ice.gov",
            "deadline": "Deadlines in removal cases are short and unforgiving — "
                        "get counsel within days, not weeks",
        },
    ],
    Domain.ECONOMIC: [
        {
            "law": "Fair hearing rights (benefits denials)",
            "covers": "If SNAP, Medicaid, TANF, or housing assistance is denied, "
                      "reduced, or cut off, you have the right to written notice "
                      "and to appeal to a fair hearing.",
            "agency": "The appeal address is on your denial letter; legal aid can represent you free",
            "deadline": "Often 10–90 DAYS from the notice — check the letter immediately",
        },
        {
            "law": "Equal Credit Opportunity Act",
            "covers": "Discrimination in loans, credit, and lending terms because "
                      "of race, national origin, sex, age, or public assistance income.",
            "agency": "CFPB — consumerfinance.gov/complaint, 1-855-411-2372",
            "deadline": "Generally 5 years",
        },
    ],
}
# Discrimination cuts across settings — reuse the hooks for where it happened
LEGAL_HOOKS[Domain.DISCRIMINATION] = (
    LEGAL_HOOKS[Domain.EMPLOYMENT][:1]
    + LEGAL_HOOKS[Domain.HOUSING][:1]
    + LEGAL_HOOKS[Domain.HEALTHCARE][:1]
    + LEGAL_HOOKS[Domain.EDUCATION][:1]
)

DOCUMENTATION_CHECKLIST = """Start documenting today — evidence disappears and clocks are running:
- Write down dates, times, and places of everything that happened (start now, while it's fresh)
- Names and roles of everyone involved, and exact words used when you can recall them
- Save every email, text, letter, voicemail, photo — forward copies somewhere personal
- Names of witnesses and how to reach them
- How others in the same situation were treated differently
- Keep everything in one folder (paper or phone). Never store evidence only on a work device."""


def hooks_for(domain) -> list:
    return LEGAL_HOOKS.get(domain, [])


def format_hooks(domain) -> str:
    hooks = hooks_for(domain)
    if not hooks:
        return ("I don't have specific legal hooks mapped for this yet. "
                "A legal aid organization can assess it — see the resources list.")
    parts = []
    for h in hooks:
        parts.append(
            f"**{h['law']}**\n"
            f"  What it covers: {h['covers']}\n"
            f"  Where to file: {h['agency']}\n"
            f"  ⏰ Time limit: {h['deadline']}"
        )
    return "\n\n".join(parts)


class Agent:
    def __init__(self, model=None):
        self.model = model

    def handle(self, situation) -> str:
        default = (
            "I'm not a lawyer, and this isn't legal advice — it's the map of "
            "laws that may apply, so you walk into any legal aid office or "
            "agency knowing what to ask for.\n\n"
            f"POTENTIAL LEGAL HOOKS ({situation.domain.value}):\n\n"
            f"{format_hooks(situation.domain)}\n\n"
            f"WHAT TO DOCUMENT:\n{DOCUMENTATION_CHECKLIST}"
        )
        return speak(
            self.model,
            "david",
            f"Situation ({situation.urgency.value} urgency): {situation.summary}",
            default,
        )
