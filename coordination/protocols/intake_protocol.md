# Intake Protocol

1. The person speaks in their own words — no forms, no jargon, no
   demands for personal data. Never ask for full name, SSN, immigration
   status (beyond what routing needs), medical records, or exact address.
2. Nia classifies the situation (`agents/nia/intake.py`):
   domain, urgency, state, documented facts, squad assignment.
3. The privacy policy is set **at classification time**
   (`nia/privacy.py`): immigration → maximum privacy mode
   (no disk, no cloud model, no logs).
4. If policy allows disk, Nia writes `coordination/shared/current_case.md`.
   The file is deleted when the session ends — zero retention.
5. Crisis-level urgency puts safety first: 911 guidance precedes all
   other content in the verdict.
