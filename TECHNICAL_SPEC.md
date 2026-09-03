# NIA AI — TECHNICAL SPECIFICATION
### *Build Guide for Developers and Technical Partners*

**Version:** 1.0  
**Project:** Nia AI — Anthos Intelligence Company  
**Audience:** Developers, Technical Partners, Community Organizations with Tech Capacity

---

## ARCHITECTURE OVERVIEW

Nia is built on a **multi-agent coordination pattern** where a central Chief of Staff agent (Nia herself) manages intake, triage, and synthesis, while specialized squad agents handle domain-specific depth.

```
┌─────────────────────────────────────────────────────────┐
│                     USER INTERFACE                       │
│            (Web | SMS | WhatsApp | CLI | API)           │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  NIA — CHIEF OF STAFF                    │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   INTAKE    │  │    TRIAGE    │  │    VERDICT    │  │
│  │  classifier │  │  router      │  │  synthesizer  │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└──────┬───────────────┬──────────────────────────────────┘
       │               │
  ┌────┘    ┌──────────┴──────────┐
  ▼         ▼                     ▼
KEISHA    PAMELA / MIKE       DAVID / KELLY
(intake)  (policy/intel)      (legal/economic)
  │         │                     │
  └─────────┴─────────────────────┘
                    │
              ┌─────▼──────┐
              │ KNOWLEDGE  │
              │    BASE    │
              │ (per domain│
              │  per state)│
              └────────────┘
```

---

## TECHNOLOGY STACK

### Recommended Stack (Privacy-First / Low-Cost)

```yaml
Base Model:
  local: ollama/llama3 or ollama/mistral     # Free, runs on most hardware
  cloud: anthropic/claude-sonnet-4-6          # Best reasoning, accessible API
  hybrid: local for sensitive, cloud for research

Agent Framework:
  option_a: Custom Python (recommended for control)
  option_b: LangChain (faster to build, more dependencies)
  option_c: File-based coordination (Nia's current architecture)

Interface:
  web: Next.js (React) or plain HTML/JS
  sms: Twilio (highest reach in underserved communities)
  whatsapp: Twilio WhatsApp API
  cli: Python Click or Typer

Database:
  resource_directory: SQLite (local) or Supabase (cloud)
  knowledge_base: ChromaDB or FAISS (vector search, local)
  user_sessions: In-memory only (no persistent user data by default)

Deployment:
  local: Docker + Ollama on community organization hardware
  cloud: Railway, Render, or Fly.io (low-cost, easy deploy)
  edge: Cloudflare Workers (for lightweight interface layers)
```

### Minimum Hardware for Local Deployment
```
RAM: 16GB minimum (32GB recommended)
Storage: 50GB minimum
GPU: Optional but helpful (Apple Silicon M-series works well)
OS: Linux (preferred), macOS, Windows WSL2
```

---

## FILE STRUCTURE

```
nia-ai/
├── README.md
├── MISSION_CHARTER.md
├── IMPLEMENTATION_ROADMAP.md
├── TECHNICAL_SPEC.md
├── CONTRIBUTING.md
├── PRIVACY_POLICY.md
│
├── agents/
│   ├── nia/
│   │   ├── SOUL.md              # Nia's core persona
│   │   ├── agent.py             # Core agent logic
│   │   ├── intake.py            # Situation classification
│   │   ├── triage.py            # Squad routing logic
│   │   └── verdict.py           # Response synthesis
│   │
│   ├── keisha/
│   │   ├── SOUL.md
│   │   └── agent.py
│   │
│   ├── pamela/
│   │   ├── SOUL.md
│   │   └── agent.py
│   │
│   ├── mike/
│   │   ├── SOUL.md
│   │   ├── agent.py
│   │   └── monitors/            # Policy monitoring scripts
│   │       ├── federal_register.py
│   │       ├── state_legislature.py
│   │       └── court_decisions.py
│   │
│   ├── david/
│   │   ├── SOUL.md
│   │   └── agent.py
│   │
│   └── kelly/
│       ├── SOUL.md
│       └── agent.py
│
├── knowledge/
│   ├── rights/
│   │   ├── federal/
│   │   │   ├── civil_rights_act.md
│   │   │   ├── fair_housing_act.md
│   │   │   ├── title_vii.md
│   │   │   ├── ada.md
│   │   │   └── immigration_rights.md
│   │   └── states/
│   │       ├── AL.md
│   │       ├── CA.md
│   │       └── ... (all 50 states)
│   │
│   ├── resources/
│   │   ├── national/
│   │   │   ├── legal_aid.json
│   │   │   ├── healthcare.json
│   │   │   ├── housing.json
│   │   │   ├── immigration.json
│   │   │   └── economic.json
│   │   └── local/
│   │       └── ... (by city)
│   │
│   └── policy_tracker/
│       ├── active_threats.md    # Laws/rules currently being changed
│       ├── anti_dei_bills.md    # State-by-state tracker
│       └── court_watch.md      # Pending cases affecting civil rights
│
├── tools/
│   ├── intake_form.py           # Structured situation intake
│   ├── document_generator.py    # Situation summary for attorneys
│   ├── resource_router.py       # Match situation to resources
│   ├── appeal_generator.py      # Insurance/benefits appeal letters
│   └── complaint_builder.py     # EEOC / HUD / OCR complaint guides
│
├── interface/
│   ├── web/                     # Next.js or plain HTML interface
│   ├── sms/                     # Twilio SMS handler
│   └── cli/                     # Command-line interface
│
├── coordination/
│   ├── shared/                  # Shared state files between agents
│   │   ├── current_case.md      # Active situation being handled
│   │   ├── handoff.md           # Agent handoff notes
│   │   └── verdict.md           # Nia's final synthesis
│   └── protocols/
│       ├── intake_protocol.md
│       ├── handoff_protocol.md
│       └── escalation_protocol.md
│
└── tests/
    ├── scenarios/               # Real-world test cases
    │   ├── housing_discrimination.md
    │   ├── healthcare_denial.md
    │   ├── workplace_discrimination.md
    │   ├── immigration_enforcement.md
    │   └── school_censorship.md
    └── test_runner.py
```

---

## CORE AGENT IMPLEMENTATION

### Nia Core Agent (`agents/nia/agent.py`)

```python
"""
Nia — Chief of Staff Agent
Core intake, triage, and verdict logic
"""

from enum import Enum
from dataclasses import dataclass
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
    CRISIS = "crisis"        # Immediate danger, detention, eviction today
    HIGH = "high"            # Time-sensitive, legal deadlines approaching
    MEDIUM = "medium"        # Important but not immediate
    LOW = "low"              # Information, education, planning


@dataclass
class Situation:
    raw_input: str
    domain: Domain
    urgency: Urgency
    summary: str
    state: Optional[str]
    documented_facts: list[str]
    squad_assignment: list[str]


class NiaAgent:
    """
    Nia's core processing logic.
    Takes raw user input and produces a structured situation
    with routing to appropriate squad agents.
    """

    def __init__(self, model_client):
        self.model = model_client
        self.soul = self._load_soul()

    def _load_soul(self) -> str:
        with open("agents/nia/SOUL.md", "r") as f:
            return f.read()

    def intake(self, user_input: str) -> Situation:
        """Classify and structure the incoming situation."""
        prompt = f"""
{self.soul}

A person has come to you with this situation:
---
{user_input}
---

Your job right now is ONLY to understand and classify what they're describing.
Do NOT jump to solutions yet.

Respond in this exact JSON format:
{{
    "domain": "healthcare|housing|employment|education|immigration|economic|discrimination|unknown",
    "urgency": "crisis|high|medium|low",
    "summary": "A 2-3 sentence plain-language summary of the situation",
    "state": "Two-letter state code if mentioned, or null",
    "documented_facts": ["fact 1", "fact 2", ...],
    "squad_needed": ["keisha", "david", "kelly"] // which agents should handle this
}}
"""
        response = self.model.complete(prompt)
        return self._parse_situation(user_input, response)

    def triage(self, situation: Situation) -> dict:
        """Route to appropriate squad agents and gather their responses."""
        responses = {}
        for agent_name in situation.squad_assignment:
            agent = self._load_agent(agent_name)
            responses[agent_name] = agent.handle(situation)
        return responses

    def verdict(self, situation: Situation, squad_responses: dict) -> str:
        """
        Synthesize squad responses into a single clear, warm, actionable response.
        This is Nia's final word to the person.
        """
        prompt = f"""
{self.soul}

Someone came to you with this situation:
{situation.summary}

Urgency: {situation.urgency.value}
Domain: {situation.domain.value}

Your squad has gathered this information:
{self._format_squad_responses(squad_responses)}

Now synthesize everything into a single response to this person.

Your response must:
1. Start by acknowledging what they're going through (1-2 sentences, warm)
2. Tell them what you found out (plain language, no jargon)
3. Give them clear next steps (numbered, concrete)
4. Tell them who to contact and how
5. Tell them what to document or keep

Remember: They may be scared. They may not have much time or resources.
Make every word count for them.
"""
        return self.model.complete(prompt)

    def _parse_situation(self, raw_input: str, model_response: str) -> Situation:
        import json
        data = json.loads(model_response)
        return Situation(
            raw_input=raw_input,
            domain=Domain(data["domain"]),
            urgency=Urgency(data["urgency"]),
            summary=data["summary"],
            state=data.get("state"),
            documented_facts=data.get("documented_facts", []),
            squad_assignment=data.get("squad_needed", ["keisha"])
        )

    def _load_agent(self, name: str):
        # Dynamic agent loading by name
        import importlib
        module = importlib.import_module(f"agents.{name}.agent")
        return module.Agent(self.model)

    def _format_squad_responses(self, responses: dict) -> str:
        return "\n\n".join([
            f"[{agent.upper()}]: {response}"
            for agent, response in responses.items()
        ])
```

---

## KNOWLEDGE BASE STRUCTURE

### Rights Document Template (`knowledge/rights/federal/fair_housing_act.md`)

```markdown
# Fair Housing Act — Plain Language Guide
**Last Updated:** [Date]  
**Reading Level Target:** 6th grade  
**Review Status:** [Reviewed by: Legal Aid Partner, Date]

## What Is It?
The Fair Housing Act is a federal law that says landlords, banks, and
real estate agents cannot treat you differently because of your:
- Race or skin color
- Religion
- National origin (where you or your family are from)
- Sex or gender
- Disability
- Whether you have children (called "familial status")

## What Does "Treat You Differently" Mean?
They cannot:
- Refuse to rent or sell to you
- Charge you more than other people
- Tell you a place is unavailable when it isn't
- Offer you worse terms or conditions
- Refuse to make reasonable accommodations for a disability
- Threaten, harass, or intimidate you

## What Counts as Evidence?
If you think this happened to you, try to document:
- Dates and times of everything that happened
- Names of anyone you spoke to
- Exact words they used (write them down right after)
- Any emails, texts, or written communication
- Names of any witnesses
- How other people were treated differently

## What Can You Do?
1. **File a complaint with HUD** — You have 1 year from the incident
   - Website: hud.gov/program_offices/fair_housing
   - Phone: 1-800-669-9777 (free)
   - You can file even if you're not a citizen

2. **Contact a local fair housing organization** — They can help you file
   at no cost and may take your case

3. **Talk to a lawyer** — Many fair housing lawyers work for free
   (called "contingency") and only get paid if you win

## Time Limits — IMPORTANT
- HUD complaint: **1 year** from when it happened
- Federal court lawsuit: **2 years**
- Don't wait — evidence disappears and memories fade

## Resources
- National Fair Housing Alliance: nationalfairhousing.org
- HUD Fair Housing: hud.gov/fairhousing
- [LOCAL RESOURCES — populated by localization layer]
```

---

## PRIVACY SPECIFICATION

This is not optional. This is foundational.

### Data Minimization
```
Rule: Collect only what is necessary to help the person in front of you.
      No more. No exceptions.

DO collect (temporarily, session only):
  - The situation description (to help them)
  - State/city (to route to local resources)
  - Contact info ONLY if they explicitly ask for follow-up

DO NOT collect:
  - Full name (use first name only if needed)
  - Social Security Number
  - Immigration status beyond what's needed to route resources
  - Medical records or diagnoses
  - Criminal history
  - Financial account information
  - Location beyond city/state
```

### Data Retention
```
Default: ZERO retention after session ends.

If user opts into follow-up:
  - Store only: contact method, domain, rough summary
  - Encrypt at rest using AES-256
  - Delete automatically after 90 days
  - Never share with third parties, law enforcement, or government agencies
```

### Immigration Tool — Maximum Privacy Mode
```
For any immigration-related interaction:
  - No logs whatsoever
  - No session storage
  - No analytics
  - HTTPS only
  - Consider Tor-accessible .onion address for highest-risk users
  - Warn users about device security before they share anything sensitive
```

### Security Requirements
```bash
# Minimum security checklist
- [ ] HTTPS everywhere (TLS 1.3)
- [ ] No third-party analytics scripts (no Google Analytics, Meta Pixel, etc.)
- [ ] Content Security Policy headers configured
- [ ] Rate limiting on all endpoints
- [ ] No user-identifying information in logs
- [ ] Regular dependency security audits
- [ ] Penetration test before any production deployment
- [ ] Clear data deletion process documented and tested
```

---

## SQUAD COORDINATION PROTOCOL

### File-Based Coordination (Current Architecture)

Agents communicate through shared markdown files in a coordination directory:

```
coordination/shared/
├── current_case.md      # Active situation — written by Nia on intake
├── keisha_notes.md      # Keisha's intake observations
├── mike_intel.md        # Mike's policy/threat findings
├── david_legal.md       # David's legal analysis
├── kelly_resources.md   # Kelly's economic resources
└── verdict.md           # Nia's final synthesis
```

**Handoff Protocol:**
1. Nia writes `current_case.md` after intake
2. Assigned agents read `current_case.md`, write their findings to their files
3. Nia reads all agent files, synthesizes into `verdict.md`
4. Interface layer reads `verdict.md` and delivers to user

---

## TESTING WITH REAL SCENARIOS

Test Nia against these scenarios before deploying any feature:

```markdown
# Scenario 1: Maternal Healthcare Discrimination
"I am 32 weeks pregnant. I went to the hospital because I was having
bad headaches and swelling. The nurse kept dismissing me and told me
it was normal. I told her I was scared and she said I was overreacting.
I am Black. I don't know if this is discrimination but I'm scared
something is wrong with me or my baby."

Expected: Crisis-level urgency | Healthcare domain
Keisha leads intake | David documents | Pamela provides rights info
Resources: local maternal health advocates, OB options, complaint pathway

# Scenario 2: School DEI Curriculum Suppression
"My daughter's school in Florida just told parents that they removed
all the Black History Month materials and the teacher who ran the
multicultural club was let go. My daughter is in 4th grade and she
came home crying saying they told her class they can't talk about
slavery anymore. What can I do?"

Expected: High urgency | Education domain
David leads (legal) | Mike provides policy context | Pamela documents
Resources: ACLU Florida, local school board procedures, state AG

# Scenario 3: ICE Enforcement
"ICE came to my neighbor's house this morning. He has been here for
15 years. His kids were born here. They took him. What can we do?
His wife doesn't speak English well. She is terrified."

Expected: Crisis urgency | Immigration domain | Maximum privacy mode
Keisha leads (de-escalation) | David routes to immigration attorneys
Resources: immigration legal aid, ICE detainee locator, family support

# Scenario 4: Workplace Discrimination
"I have been at my job for 6 years. I am the only Black woman on my
team. I just found out that two white men hired after me make $15,000
more than me. When I brought it up to HR they said it was based on
'market rates' and then two weeks later I got a bad performance review
for the first time ever. I think they are retaliating."

Expected: High urgency | Employment domain
David leads (legal) | Kelly documents (wage gap) | Mike checks retaliation laws
Resources: EEOC, employment lawyers, documentation guide
```

---

## DEPLOYMENT CHECKLIST

Before any deployment, confirm:

```
PRIVACY
- [ ] Zero data retention by default
- [ ] Immigration tool in maximum privacy mode
- [ ] No third-party scripts loading on any page
- [ ] SSL/TLS configured correctly
- [ ] Privacy policy reviewed by community members

ACCESSIBILITY
- [ ] Tested at 6th-grade reading level (use Hemingway App)
- [ ] Works on slow 3G connection
- [ ] Works on 5-year-old Android phone
- [ ] Spanish language version available or roadmapped
- [ ] Screen reader compatible

ACCURACY
- [ ] All know-your-rights content reviewed by a legal professional
- [ ] All resource links checked and working
- [ ] State-specific information verified for deployment state
- [ ] Dated and versioned so users know how current the info is

COMMUNITY
- [ ] At least 2 community partners aware and supportive
- [ ] Feedback mechanism in place
- [ ] Clear escalation path for situations Nia can't handle
- [ ] Human backup for crisis situations
```

---

## CONTRIBUTING

See `CONTRIBUTING.md` for detailed contribution guidelines.

**Quick start for developers:**

```bash
git clone https://github.com/TushaeBXN/nia-ai
cd nia-ai
cp .env.example .env       # Add your API key or Ollama endpoint
pip install -r requirements.txt
python -m nia.cli          # Run Nia in CLI mode
```

---

**Nia AI | Anthos Intelligence Company**  
*Built for Justice. Built for Purpose.*
