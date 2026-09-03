"""
Nia — Situation Intake (Phase 1, Core Capability)

Takes a person's own words and produces a structured Situation:
domain, urgency, summary, state, documented facts, squad assignment.

Two pathways:
  1. Model-backed classification (Ollama or Claude) — richer summaries.
  2. Deterministic keyword fallback — always available, no model needed,
     and the safety net whenever model output can't be parsed.

Intake must never crash. Someone in crisis gets routed either way.
"""

import json
import re
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional


class Domain(Enum):
    HEALTHCARE = "healthcare"
    HOUSING = "housing"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    IMMIGRATION = "immigration"
    ECONOMIC = "economic"
    DISCRIMINATION = "discrimination"
    UNKNOWN = "unknown"


class Urgency(Enum):
    CRISIS = "crisis"    # Immediate danger, detention, eviction today
    HIGH = "high"        # Time-sensitive, legal deadlines approaching
    MEDIUM = "medium"    # Important but not immediate
    LOW = "low"          # Information, education, planning


@dataclass
class Situation:
    raw_input: str
    domain: Domain
    urgency: Urgency
    summary: str
    state: Optional[str]
    documented_facts: list
    squad_assignment: list

    def to_dict(self) -> dict:
        d = asdict(self)
        d["domain"] = self.domain.value
        d["urgency"] = self.urgency.value
        return d


# Which squad agents handle which domain (leads first).
# Derived from the TECHNICAL_SPEC test scenarios.
DOMAIN_SQUAD = {
    Domain.HEALTHCARE: ["keisha", "david", "pamela"],
    Domain.HOUSING: ["david", "pamela"],
    Domain.EMPLOYMENT: ["david", "kelly", "mike"],
    Domain.EDUCATION: ["david", "mike", "pamela"],
    Domain.IMMIGRATION: ["keisha", "david"],
    Domain.ECONOMIC: ["kelly", "pamela"],
    Domain.DISCRIMINATION: ["david", "keisha"],
    Domain.UNKNOWN: ["keisha"],
}


# ─── Deterministic fallback classifier ──────────────────────────────────────

DOMAIN_KEYWORDS = {
    Domain.HEALTHCARE: [
        "hospital", "doctor", "nurse", "medical", "pregnan", "clinic",
        "medicaid", "medicare", "diagnos", "prescription", "patient",
        "health insurance", "emergency room", r"\ber\b", "symptom",
    ],
    Domain.HOUSING: [
        "landlord", "rent", "lease", "evict", "apartment", "housing",
        "tenant", "mortgage", "foreclos", r"\bhud\b", "section 8",
    ],
    Domain.EMPLOYMENT: [
        r"\bjob\b", r"\bwork\b", r"\bboss\b", "fired", r"\bhr\b", "wage",
        "paycheck", "coworker", "promotion", "hired", "salary",
        "performance review", "employer", "workplace", r"\bteam\b",
    ],
    Domain.EDUCATION: [
        "school", "teacher", "student", "college", r"\bclass\b",
        "curriculum", "principal", r"\bgrade\b", "university", "fafsa",
        "financial aid", "scholarship",
    ],
    Domain.IMMIGRATION: [
        r"\bice\b", "immigra", "deport", r"\bvisa\b", "green card",
        "undocumented", "asylum", "detain", "citizenship", "border",
    ],
    Domain.ECONOMIC: [
        "benefits", "snap", "food stamps", "debt", r"\bloan\b", "credit",
        "small business", r"\bbank\b", "welfare", r"\btanf\b",
        "unemployment", r"\bbills\b", r"\beitc\b",
    ],
    Domain.DISCRIMINATION: [
        "discriminat", "racis", "profil", r"\bbias\b", "civil rights",
        "because i'm black", "because i am black", "treated differently",
        "harass",
    ],
}

# Crisis: immediate danger, detention, imminent loss of home, medical emergency
CRISIS_PATTERNS = [
    r"\bice\b.{0,60}\b(came|come|took|raid|detain)",
    r"\b(took|detained|arrested)\s+(him|her|them|my)\b",
    r"deportation order",
    r"evict\w*\s+(today|tomorrow|tonight|this week)",
    r"locked (me )?out",
    r"(bleeding|can'?t breathe|chest pain|unconscious)",
    r"pregnan.*\b(headache|swell|bleed|pain|dizz|vision|scared)",
    r"\b(headache|swell|bleed)\w*.*pregnan",
    r"afraid for (my|our) (life|lives|safety)",
    r"\bsuicid",
    r"domestic violence",
]

# High: time-sensitive, deadlines, retaliation, active loss
HIGH_PATTERNS = [
    r"retaliat", r"deadline", r"court date", r"\bhearing\b",
    r"eviction notice", r"\bnotice\b", r"\bfired\b", r"let go",
    r"suspended", r"expelled", r"\bbanned\b", r"\bremoved\b",
    r"denied", r"cut off", r"this (week|month)",
]

# Low: informational, no active incident
LOW_PATTERNS = [
    r"^(what|how|when|where|who|can you (explain|tell))\b",
    r"\b(learn|understand|curious|planning ahead)\b",
]

US_STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT",
    "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI",
    "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME",
    "maryland": "MD", "massachusetts": "MA", "michigan": "MI",
    "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
    "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND",
    "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
}


def _score_domains(text: str) -> dict:
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for kw in keywords:
            pattern = kw if kw.startswith(r"\b") or "\\" in kw else re.escape(kw)
            score += len(re.findall(pattern, text))
        scores[domain] = score
    return scores


def classify_fallback(user_input: str) -> dict:
    """Keyword classification — no model required."""
    # Collapse whitespace so patterns match across line breaks
    text = re.sub(r"\s+", " ", user_input.lower())

    scores = _score_domains(text)
    discrimination_score = scores.pop(Domain.DISCRIMINATION)
    best_domain = max(scores, key=scores.get)
    if scores[best_domain] == 0:
        best_domain = Domain.DISCRIMINATION if discrimination_score else Domain.UNKNOWN

    urgency = Urgency.MEDIUM
    if any(re.search(p, text) for p in CRISIS_PATTERNS):
        urgency = Urgency.CRISIS
    elif any(re.search(p, text) for p in HIGH_PATTERNS):
        urgency = Urgency.HIGH
    elif any(re.search(p, text) for p in LOW_PATTERNS) or best_domain == Domain.UNKNOWN:
        urgency = Urgency.LOW

    state = None
    for name, code in US_STATES.items():
        if re.search(r"\b" + name + r"\b", text):
            state = code
            break

    # Facts: the person's own sentences, kept in order
    facts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", user_input.strip()) if s.strip()]

    return {
        "domain": best_domain.value,
        "urgency": urgency.value,
        "summary": " ".join(facts[:3])[:400],
        "state": state,
        "documented_facts": facts,
        "squad_needed": [a for a in DOMAIN_SQUAD[best_domain]],
    }


# ─── Model-backed classification ────────────────────────────────────────────

INTAKE_PROMPT = """A person has come to you with this situation:
---
{user_input}
---

Your job right now is ONLY to understand and classify what they're describing.
Do NOT jump to solutions yet.

Respond with ONLY a JSON object in this exact format, nothing else:
{{
    "domain": "healthcare|housing|employment|education|immigration|economic|discrimination|unknown",
    "urgency": "crisis|high|medium|low",
    "summary": "A 2-3 sentence plain-language summary of the situation",
    "state": "Two-letter US state code if mentioned, or null",
    "documented_facts": ["fact 1", "fact 2"],
    "squad_needed": ["keisha", "david"]
}}"""


def extract_json(text: str) -> Optional[dict]:
    """Pull the first JSON object out of model output (fences, prose, etc.)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def intake(user_input: str, model=None, soul: str = "") -> Situation:
    """
    Classify and structure an incoming situation.
    Uses the model when available; falls back to keywords otherwise.
    """
    data = None
    if model is not None:
        try:
            response = model.complete(
                INTAKE_PROMPT.format(user_input=user_input), system=soul or None
            )
            data = extract_json(response)
        except Exception:
            data = None  # never let intake crash — fall back

    fallback = classify_fallback(user_input)
    if data is None:
        data = fallback

    def _enum(cls, value, default):
        try:
            return cls(str(value).lower().strip())
        except ValueError:
            return default

    domain = _enum(Domain, data.get("domain"), Domain(fallback["domain"]))
    urgency = _enum(Urgency, data.get("urgency"), Urgency(fallback["urgency"]))

    valid_agents = {"keisha", "pamela", "mike", "david", "kelly"}
    squad = [a for a in data.get("squad_needed", []) if a in valid_agents]
    if not squad:
        squad = DOMAIN_SQUAD[domain]

    state = data.get("state")
    if state is not None:
        state = str(state).strip().upper()
        if state not in US_STATES.values():
            state = fallback["state"]

    return Situation(
        raw_input=user_input,
        domain=domain,
        urgency=urgency,
        summary=data.get("summary") or fallback["summary"],
        state=state,
        documented_facts=data.get("documented_facts") or fallback["documented_facts"],
        squad_assignment=squad,
    )
