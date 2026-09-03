"""
Skill registry — maps skills to Nia's squad agents and domains.

Each entry defines:
  - squad: which agent(s) own this skill
  - domains: which situation domains trigger it
  - trigger: natural language patterns that invoke the skill
  - action: what Nia should DO with the skill output
"""

from enum import Enum


class Squad(str, Enum):
    KELLY = "kelly"      # Economic empowerment, benefits, money, resources
    DAVID = "david"      # Legal, rights, documentation, formation
    MIKE = "mike"        # Research, intelligence, news, company data
    PAMELA = "pamela"    # Policy translation, community proposals
    KEISHA = "keisha"    # Intake, crisis, outreach, communication
    NIA = "nia"          # Coordination — multi-squad situations


# Skill → squad + domain mappings
SKILL_MAP = {

    # --- COMMUNITY + SOCIAL IMPACT ---
    "grant-finder": {
        "squad": [Squad.KELLY],
        "domains": ["economic", "housing", "education", "food", "veterans", "nonprofit"],
        "trigger": [
            "find grants", "are there grants", "what funding", "help me find money",
            "what grants exist", "funding for my nonprofit", "grants for veterans"
        ],
        "action": (
            "Search federal (grants.gov), state, local, and foundation grant programs. "
            "Return a ranked list with: grant name, funder, max amount, deadline, "
            "eligibility, and application link. Prioritize grants the user can apply to now."
        ),
        "search_strategy": [
            "grants.gov [mission keyword] [state]",
            "[state] [sector] grant program 2026",
            "[city] community foundation grants",
            "USDA HUD SBA NEA [sector] grant program",
            "national foundation [mission] grants",
        ],
    },

    "veteran-resource-finder": {
        "squad": [Squad.KELLY, Squad.DAVID],
        "domains": ["veterans", "healthcare", "housing", "economic", "mental_health"],
        "trigger": [
            "find veteran benefits", "what help for veterans", "my dad is a veteran",
            "find VA programs", "veteran services near", "disabled veteran programs",
            "homeless veteran", "elderly veteran"
        ],
        "action": (
            "Find every applicable VA benefit, state veteran program, VSO chapter, "
            "and nonprofit resource for this veteran's specific situation (era served, "
            "disability rating, state, primary need). Provide direct contacts and next steps."
        ),
        "search_strategy": [
            "VA benefits [need] [era]",
            "[state] veteran benefits [need]",
            "VSO VFW American Legion DAV [city]",
            "Wounded Warrior Bob Woodruff Gary Sinise [need]",
        ],
    },

    "senior-services-mapper": {
        "squad": [Squad.KELLY],
        "domains": ["healthcare", "housing", "economic", "food"],
        "trigger": [
            "help for elderly", "senior services", "my mom is elderly", "senior care",
            "elder resources", "aging parent", "nursing home alternative"
        ],
        "action": (
            "Map all elder care resources: Medicare/Medicaid coverage, Area Agency on Aging, "
            "Meals on Wheels, senior housing programs, PACE programs, caregiver support, "
            "and state-specific elder services. Provide local contacts."
        ),
    },

    "nonprofit-formation-guide": {
        "squad": [Squad.DAVID],
        "domains": ["economic", "community", "education", "housing"],
        "trigger": [
            "start a nonprofit", "form a 501c3", "tax-exempt status", "charitable organization",
            "nonprofit for my community", "how do I get nonprofit status"
        ],
        "action": (
            "Walk through every step: mission statement, board formation, articles of incorporation "
            "(state-specific), bylaws, EIN application, IRS Form 1023/1023-EZ, state registration, "
            "and ongoing compliance. Flag state-specific requirements."
        ),
    },

    "community-proposal-writer": {
        "squad": [Squad.PAMELA, Squad.DAVID],
        "domains": ["housing", "economic", "community", "education"],
        "trigger": [
            "city owns this building", "surplus property", "public building",
            "propose community use", "government property", "abandoned school library"
        ],
        "action": (
            "Write a formal Community Use Proposal: executive summary, mission alignment, "
            "community benefit statement, proposed use plan, economic impact, references, "
            "and a cover letter addressed to the relevant city/county department."
        ),
    },

    # --- FINANCIAL + LEGAL + REAL ESTATE ---
    "financial-model-builder": {
        "squad": [Squad.KELLY],
        "domains": ["economic", "housing", "nonprofit"],
        "trigger": [
            "financial model", "revenue projections", "3-year P&L", "model out the financials",
            "cash flow", "break-even analysis", "budget for my nonprofit", "pro forma"
        ],
        "action": (
            "Build a financial model as an Excel workbook (Python/openpyxl). "
            "Sheets: Assumptions, P&L or Cash Flow, Charts. Document every assumption clearly. "
            "Adapt to the entity type: startup, nonprofit, real estate, project budget."
        ),
    },

    "real-estate-analyzer": {
        "squad": [Squad.KELLY],
        "domains": ["housing", "economic"],
        "trigger": [
            "analyze this property", "what's this building worth", "research this address",
            "good investment property", "real estate market in", "comparable sales"
        ],
        "action": (
            "Research: current listing (LoopNet/Crexi/Zillow), county tax records (assessed value, "
            "last sale, owner), comparable sales, zoning, neighborhood economic context. "
            "Produce a 1-page property analysis with opportunity/risk summary."
        ),
    },

    "contract-generator": {
        "squad": [Squad.DAVID],
        "domains": ["employment", "economic", "housing"],
        "trigger": [
            "draft a contract", "I need a contract for", "service agreement",
            "freelance contract", "vendor agreement", "lease agreement"
        ],
        "action": (
            "Draft a complete contract with: parties, scope/services, compensation, "
            "term, termination clause, IP/ownership, dispute resolution, governing law. "
            "Flag any clauses the user should have an attorney review."
        ),
    },

    # --- RESEARCH + INTELLIGENCE ---
    "ai-research-assistant": {
        "squad": [Squad.MIKE],
        "domains": ["all"],
        "trigger": [
            "research", "deep dive into", "find everything about", "investigate",
            "what do you know about", "compile information on"
        ],
        "action": (
            "Run 5-10 targeted searches. Synthesize findings with citations. "
            "Structure output: key facts, timeline if relevant, opportunities, risks, "
            "gaps in available information, and recommended next steps."
        ),
    },

    "company-research": {
        "squad": [Squad.MIKE],
        "domains": ["employment", "economic"],
        "trigger": [
            "research this company", "find out about", "who is this company",
            "company background", "is this employer legit"
        ],
        "action": (
            "Research: company status (Secretary of State), principals, products/services, "
            "financials if public, news and press coverage, reviews (Glassdoor), "
            "any complaints or legal actions. Flag red flags."
        ),
    },

    "news-monitor": {
        "squad": [Squad.MIKE],
        "domains": ["all"],
        "trigger": [
            "what's the latest on", "catch me up on", "what's been happening with",
            "monitor news", "recent developments", "what did I miss about"
        ],
        "action": (
            "Run 3-6 searches across time windows (today, last week, last month). "
            "Synthesize: what changed, what matters, what's coming. "
            "Keep it scannable — what the user needs to know, not everything that was written."
        ),
    },

    "location-story-mapper": {
        "squad": [Squad.MIKE, Squad.PAMELA],
        "domains": ["housing", "economic", "community"],
        "trigger": [
            "history of this location", "what happened here", "who owns this land",
            "story of this neighborhood", "research this address history"
        ],
        "action": (
            "Research: ownership history (deed records), prior businesses or institutions, "
            "neighborhood demographics over time, economic development context, "
            "any legal or environmental history. Produce a narrative timeline."
        ),
    },

    # --- WRITING + COMMUNICATION ---
    "email-drafter": {
        "squad": [Squad.KEISHA],
        "domains": ["all"],
        "trigger": [
            "draft an email", "write an email", "help me respond to", "email to my landlord",
            "email to my employer", "outreach email", "follow-up email"
        ],
        "action": (
            "Draft a clear, professional email. Subject line + body. "
            "Adapt tone to situation: firm for disputes, warm for outreach, formal for legal. "
            "Flag anything the user should verify before sending."
        ),
    },

    "meeting-brief": {
        "squad": [Squad.KEISHA, Squad.NIA],
        "domains": ["all"],
        "trigger": [
            "prep for my meeting", "meeting brief", "I have a meeting about",
            "what should I say in my meeting", "help me prepare"
        ],
        "action": (
            "Produce a 1-page meeting brief: situation summary, user's goals, "
            "key talking points, questions to ask, what to watch for, and what to avoid saying."
        ),
    },

    "partnership-outreach": {
        "squad": [Squad.KEISHA, Squad.NIA],
        "domains": ["economic", "community"],
        "trigger": [
            "reach out to partners", "partnership email", "collaboration outreach",
            "introduce my organization", "business development email"
        ],
        "action": (
            "Research the target organization first. Then draft: a personalized opening "
            "that references their specific work, a clear value proposition, "
            "a concrete ask, and a low-friction next step."
        ),
    },

    # --- RESEARCH + DOCUMENTS WORKFLOW ---
    "research-to-documents": {
        "squad": [Squad.NIA],
        "domains": ["housing", "economic", "community"],
        "trigger": [
            "research this and help me acquire", "look into this property",
            "find out everything about and make a plan", "research and create documents",
            "I want to buy this", "help me figure out this opportunity"
        ],
        "action": (
            "Full 5-phase workflow: understand the opportunity → deep web research (5-15 searches) "
            "→ synthesize findings → offer document options (LOI, business plan, grant strategy, "
            "pitch deck) → produce the chosen documents. This is the highest-leverage skill for "
            "acquisition, launch, and community impact projects."
        ),
    },

    # --- TECHNICAL ---
    "code-debugger": {
        "squad": [Squad.MIKE],
        "domains": ["all"],
        "trigger": [
            "this code isn't working", "fix this bug", "error in my code",
            "debug this", "why is this failing", "help me fix this script"
        ],
        "action": (
            "Identify root cause → explain clearly → fix the code → write a test. "
            "Always explain WHY it broke, not just what changed."
        ),
    },

    "data-pipeline-builder": {
        "squad": [Squad.MIKE],
        "domains": ["all"],
        "trigger": [
            "clean this CSV", "transform this data", "build a script to process",
            "convert this Excel to JSON", "pull data from API", "ETL pipeline"
        ],
        "action": (
            "Define source + destination → choose the right tool (pandas, csv, requests, psycopg2) "
            "→ write the script → test with sample data → document assumptions."
        ),
    },

    "api-integrator": {
        "squad": [Squad.MIKE],
        "domains": ["all"],
        "trigger": [
            "connect to this API", "integrate with", "fetch data from", "build an API client",
            "how do I use the API", "pull data from this service"
        ],
        "action": (
            "Fetch the API docs first → write the integration → test live → "
            "handle auth, rate limits, and error cases. Return working, runnable code."
        ),
    },

    "ai-chatbot-builder": {
        "squad": [Squad.MIKE, Squad.NIA],
        "domains": ["all"],
        "trigger": [
            "build me a chatbot", "create an AI assistant", "make an interactive AI tool",
            "Claude-powered chat interface", "AI that can answer questions about"
        ],
        "action": (
            "Define the chatbot (purpose, users, scope, tone) → design system prompt "
            "→ build as an artifact with Claude-in-Claude → test edge cases."
        ),
    },

    "data-to-report": {
        "squad": [Squad.MIKE, Squad.PAMELA],
        "domains": ["all"],
        "trigger": [
            "turn this data into a report", "make a report from", "format these findings",
            "create a document from this data", "write up these results"
        ],
        "action": (
            "Structure the data into a professional report: executive summary, "
            "key findings, supporting data, charts if applicable, recommendations. "
            "Adapt format to audience (community, legal, investor, government)."
        ),
    },

    "ui-mockup-builder": {
        "squad": [Squad.MIKE],
        "domains": ["all"],
        "trigger": [
            "build a mockup", "show me what this could look like", "wireframe for",
            "UI for my app", "design this interface", "prototype this"
        ],
        "action": (
            "Build an interactive HTML/CSS mockup as an artifact. "
            "Use the Anthos Intelligence dark design system: #050a14 ground, #4599ff blue, "
            "#29c484 teal. Mobile-first, responsive."
        ),
    },

    "task-to-project": {
        "squad": [Squad.NIA],
        "domains": ["all"],
        "trigger": [
            "turn this into a project plan", "help me plan out", "I want to do X, where do I start",
            "project plan for", "phases and milestones for"
        ],
        "action": (
            "Clarify the goal → define success criteria → break into phases "
            "→ list milestones, deliverables, and dependencies → "
            "flag blockers and risks → produce a structured project brief."
        ),
    },

    "financial-model-builder": {
        "squad": [Squad.KELLY],
        "domains": ["economic", "housing", "nonprofit"],
        "trigger": [
            "build a financial model", "revenue projections", "P&L", "cash flow model",
            "break-even", "nonprofit budget", "pro forma"
        ],
        "action": (
            "Intake: model type, revenue model, cost categories, time horizon, known assumptions. "
            "Build in Python (openpyxl): Assumptions sheet, P&L or Cash Flow sheet, Summary charts. "
            "Document every assumption. Output .xlsx."
        ),
    },

    "ai-learning-roadmap-advisor": {
        "squad": [Squad.NIA],
        "domains": ["all"],
        "trigger": [
            "how do I learn AI", "where do I start with AI", "what AI skills should I learn",
            "AI learning path", "help me get into AI", "what should I know about AI"
        ],
        "action": (
            "Walk through the Tina Huang framework: Level 1 (investment thesis, prompting, core tools), "
            "Level 2 (AI agents — web then local), Level 3 (building agents, MCPs, AI coding). "
            "Assess the user's current level and give them a specific next step."
        ),
    },
}


def skills_for_domain(domain: str) -> list:
    """Return all skills relevant to a given domain."""
    domain_lower = domain.lower()
    return [
        name for name, cfg in SKILL_MAP.items()
        if "all" in cfg["domains"] or domain_lower in cfg["domains"]
    ]


def skills_for_squad(squad: Squad) -> list:
    """Return all skills owned by a given squad agent."""
    return [
        name for name, cfg in SKILL_MAP.items()
        if squad in cfg["squad"]
    ]


def skill_prompt(skill_name: str, situation_summary: str = "") -> str:
    """Generate an action prompt for a skill given a situation."""
    cfg = SKILL_MAP.get(skill_name)
    if not cfg:
        return ""
    lines = [f"[{skill_name.upper()} SKILL]\n{cfg['action']}"]
    if situation_summary:
        lines.append(f"\nApply this to: {situation_summary}")
    if "search_strategy" in cfg:
        lines.append("\nSearch strategy:")
        for s in cfg["search_strategy"]:
            lines.append(f"  - {s}")
    return "\n".join(lines)
