# Contributing to Nia

Nia is a mission, not a product. Contributions are welcome from anyone
who shares it — you don't have to be a developer.

## The test every contribution must pass
> **Does this make a real difference in a real person's life?**

If a feature doesn't serve someone navigating a discriminatory healthcare
system, an unjust eviction, or an immigration enforcement encounter — it
is not a priority right now.

## If you're a developer
- Read `TECHNICAL_SPEC.md` and `STATUS.md` first
- Run the offline test suite before and after your change:
  `python3 -m tests.test_runner`
- Rules of the codebase:
  - **Stdlib only** for anything a user runs — the mission system must
    work on old hardware with nothing installed (heavy deps are for the
    training pipeline only)
  - **Never let intake crash** — every model call needs a deterministic
    fallback
  - **Never invent facts** — laws, deadlines, phone numbers, and orgs
    come from the knowledge base, with a `last_verified` date
  - **Privacy is enforced in code**, not policy — anything touching user
    data goes through `nia/privacy.py`, and immigration means no disk,
    no cloud, no logs

## If you're a legal professional
The highest-impact contribution right now: **review the know-your-rights
guides** in `knowledge/rights/federal/` for accuracy. Each carries a
`Review Status` header — none has been reviewed yet, and the spec
requires review before deployment.

## If you're an advocate or organizer
- Test Nia against real (anonymized) community scenarios and file issues
- Add or correct organizations in `knowledge/resources/national/`
  (name, phone, website, eligibility, what they help with)
- Tell us what's missing for your city — localization is Phase 3

## Content rules
- 6th-grade reading level, always (check with the Hemingway App)
- Dated and versioned — people need to know how current information is
- Plain language is not dumbed down; it's the gate removed

## If you have Black history source material
PDFs can be converted to training data for the Nia model itself with
`pdf_to_training.py` — see `TRAINING.md`.
