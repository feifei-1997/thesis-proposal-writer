# Architecture

## Components

```text
SKILL.md
  Agent routing, conversation policy, evidence rules
      │
      ▼
runner.py
  JSON stdin/file boundary and structured failures
      │
      ▼
main.py
  proposal brief normalization
  missing-field state machine
  literature query planning and deduplication
      │
      ▼
core/cqvip_client.py
  CQVIP authentication, HTTPS requests, normalization,
  bounded retries, response limits, and secret redaction
```

## State Transitions

```text
request
  │
  ├─ missing topic ───────────────► needs_input(topic)
  │
  ├─ missing one or more fields ──► needs_input(missing fields)
  │
  └─ complete brief
          │
          ├─ CQVIP succeeds ──────► ready_to_write + papers/citations
          └─ CQVIP unavailable ───► ready_to_write + explicit warning
```

The host Assistant must merge facts from visible conversation history into `proposal_brief` before each call. The runner is intentionally stateless and does not store user conversations.

## Evidence Boundary

Only CQVIP response fields may support concrete paper claims. Search results are metadata and abstracts unless a separate authorized full-text capability is present. The host must not infer missing DOI, author, journal, year, or page data.

## Credential Boundary

`CQVIP_API_KEY` is read at client construction time. The runner input schema does not accept an API key, and client errors replace the active key with `[REDACTED]`. Release packaging rejects a hardcoded key assignment.

## Release Boundary

The GitHub repository contains contributor documentation, examples, tests, and automation. The installable Jenius ZIP contains only:

```text
SKILL.md
main.py
runner.py
_meta.json
_skillhub_meta.json
core/
references/
```

ZIP entry names use `/` on every build platform.
