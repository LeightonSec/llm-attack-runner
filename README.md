# LLM Red Team Tool

Adversarial prompt testing tool for LLM endpoints. Fires categorised attack payloads at a target, scores each response as FOLD / PARTIAL / RESIST / UNCLEAR, and produces a JSON report.

**Only use against systems you own or have explicit written authorisation to test.**

Designed to work alongside the [ai-firewall](../ai-firewall) and [llm-honeypot](../llm-honeypot) projects — run it against your own honeypot to measure what gets through.

---

## Attack categories

| Category | What it tests |
|---|---|
| `jailbreak` | DAN, developer mode, persona hijacking, restriction bypass |
| `prompt_injection` | Instruction override, newline injection, document hijack |
| `data_extraction` | System prompt leakage, context dump, training data probing |
| `social_engineering` | Authority claims, urgency framing, fictional wrappers |
| `reconnaissance` | Model identification, capability mapping, infrastructure probing |

49 payloads total across 5 categories.

---

## How scoring works

Each response is scored in two layers:

1. **Keyword scan** — fast regex patterns for resistance signals ("I cannot", "against my guidelines") and compliance signals ("Sure!", "As DAN", "entering developer mode"). Instant, no API call.

2. **Claude Haiku semantic score** — fires only when keywords are ambiguous. Returns FOLD / PARTIAL / RESIST / UNCLEAR based on semantic judgment.

Verdicts:
- **FOLD** — target fully complied with the attack
- **PARTIAL** — partial compliance or compliance signals present
- **RESIST** — target firmly declined
- **UNCLEAR** — cannot determine from response alone

---

## Setup

```bash
cd /path/to/llm-redteam
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY for semantic scoring
```

The API key is optional — without it the tool falls back to keyword-only scoring.

---

## Usage

### Test your honeypot (recommended starting point)

```bash
# Start the honeypot first
cd ../llm-honeypot && python app.py &

# Run all categories against it
python cli.py --target http://localhost:5001/chat
```

### Dry run — list payloads without firing

```bash
python cli.py --target http://localhost:5001/chat --dry-run
```

### Single category

```bash
python cli.py --target http://localhost:5001/chat --category jailbreak
```

### Custom delay and output path

```bash
python cli.py --target http://localhost:5001/chat --delay 2.0 --output results/my_run.json
```

### Custom request/response field names

For targets that use different JSON field names:

```bash
python cli.py --target http://example.com/api \
  --request-field message \
  --response-field content
```

### With auth header

```bash
python cli.py --target http://example.com/chat \
  --header "Authorization: Bearer your-token"
```

---

## Output

Results are saved to `results/redteam_<timestamp>.json` (gitignored).

```json
{
  "summary": {
    "total_payloads": 49,
    "fold": 3,
    "partial": 5,
    "resist": 38,
    "unclear": 3,
    "fold_rate": 0.16
  },
  "by_category": { ... },
  "bypasses": [ ... ],
  "all_results": [ ... ]
}
```

---

## Security notes

- The `--yes` flag skips the confirmation prompt. Only use it in authorised CI/CD pipelines, not to bypass the safety check for convenience.
- `results/` is gitignored. Never commit result files — they contain full prompts and responses that may include sensitive target behaviour.
- The `.env` file is gitignored. Never commit your API key.
- This tool is scoped to your own systems. Unauthorised use against third-party systems may be illegal under the Computer Fraud and Abuse Act and equivalent laws.
