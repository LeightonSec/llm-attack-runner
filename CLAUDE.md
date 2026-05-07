# CLAUDE.md — LLM Red Team Tool

Adversarial prompt testing tool for LLM endpoints. Fires categorised attack payloads at a
target, scores each response as FOLD / PARTIAL / RESIST / UNCLEAR, and produces a structured
JSON report.

**Only use against systems you own or have explicit written authorisation to test.**

Designed to work alongside ai-firewall and llm-honeypot — run it against your own honeypot
to measure what gets through.

---

## SOC Toolkit Position

- **Layer:** Research (Layer 5)
- **Complements:** llm-honeypot (attack vs defence pair), ai-firewall (measures what it misses)
- **Gap it fills:** Offensive AI security testing — quantifies LLM defence effectiveness

---

## Architecture

- `cli.py` — Argument parsing, authorisation gate, dry-run mode, summary output
- `runner.py` — Campaign orchestration, HTTP firing, per-payload progress output
- `scorer.py` — Two-layer scoring: keyword regex → Claude Haiku semantic fallback
- `report.py` — Report generation, URL sanitisation, JSON output
- `payloads/*.json` — Attack payload library, 65 payloads across 5 categories

---

## Scoring Pipeline

### Layer 1 — Keyword Regex (scorer.py)
- Fast regex patterns for resistance signals and compliance signals
- Returns RESIST, FOLD, or PARTIAL immediately if unambiguous
- Returns None if ambiguous — triggers Layer 2

### Layer 2 — Claude Haiku Semantic (scorer.py)
- Fires only when keyword layer is ambiguous
- Truncates prompt and response to 400 chars each before sending
- Falls back to UNCLEAR if API unavailable or call fails
- API key optional — tool runs keyword-only without it

---

## Verdicts

| Verdict | Meaning |
|---------|---------|
| FOLD | Target fully complied with the attack |
| PARTIAL | Partial compliance or compliance signals present |
| RESIST | Target firmly declined |
| UNCLEAR | Cannot determine from response alone |
| ERROR | Network error, timeout, or connection failure |

---

## Attack Categories

| Category | Payloads | What it tests |
|----------|---------|---------------|
| jailbreak | 15 | DAN, developer mode, persona hijacking, token smuggling, restriction bypass |
| prompt_injection | 13 | Instruction override, newline injection, document hijack, structured data injection |
| data_extraction | 14 | System prompt leakage, context dump, training data probing, translation exfil |
| social_engineering | 12 | Authority claims, urgency framing, fictional wrappers, helpfulness exploitation |
| reconnaissance | 11 | Model identification, capability mapping, infrastructure probing, canary detection |

---

## Current Status

✅ Complete — LeightonSec/llm-redteam
✅ 65 payloads across 5 categories
✅ Two-layer scoring: keyword regex + Claude Haiku semantic
✅ Authorisation gate — hostname confirmation required before firing
✅ Dry-run mode — list payloads without sending requests
✅ Custom request/response field names for non-standard targets
✅ Custom auth header support
✅ Per-category breakdown in report and summary
✅ URL sanitisation — strips query params/fragments before saving to disk
✅ results/ gitignored — full prompts and responses never committed
✅ --yes flag for authorised CI pipelines only
✅ 15s request timeout with graceful error handling

---

## Known Issues

- `datetime.utcnow()` deprecated in Python 3.12+ — replace with `datetime.now(datetime.UTC)` in report.py
- In-memory only — no persistent state between runs
- Keyword patterns tuned for English — may miss non-English compliance signals

---

## Next Steps

- Expand payload library — currently 65, target 100+
- Add payload tagging for OWASP LLM Top 10 / Agentic Top 10 mapping
- HTML report output option
- Parallel firing mode with configurable concurrency
- Integration with Incident Tracker — auto-raise ticket on high fold rate

---

## Tech Stack

- Python, requests
- Anthropic Claude API (claude-haiku-4-5-20251001) — optional, semantic scoring only
- python-dotenv

---

## Security Rules

- `ANTHROPIC_API_KEY` in `.env` — never committed
- `.env`, `venv/`, `results/` gitignored — never commit result files
- Result files contain full prompts and responses — treat as sensitive
- Never use `--yes` flag except in authorised CI pipelines
- Never fire against targets you do not own or have explicit written authorisation to test
- URL sanitisation in report.py strips auth tokens from saved reports — do not remove

---

## Conventions

- Payloads in `payloads/*.json` — one file per category, follow existing schema exactly
- Payload schema: `id`, `category`, `technique`, `name`, `payload` — all fields required
- IDs follow pattern: `jb_001`, `pi_001`, `de_001`, `se_001`, `re_001`
- Scoring always runs keyword layer first — do not skip to API for speed
- API scorer truncates to 400 chars — do not increase without considering cost
- Verdicts always uppercase strings: `"FOLD"`, `"PARTIAL"`, `"RESIST"`, `"UNCLEAR"`, `"ERROR"`
- Target URL sanitised before saving — never store raw URLs with auth tokens
- TIMEOUT = 15s — do not reduce, some targets are slow to respond