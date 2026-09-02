# Thesis Proposal Writer Skill

[简体中文](README.zh-CN.md)

A Jenius-compatible Agent Skill for thesis proposal writing. It collects four essential research constraints through normal Assistant conversation, retrieves literature metadata from CQVIP, and prepares an evidence bundle that the host Assistant uses to draft the proposal.

> This is an independent community project. It is not affiliated with or endorsed by CQVIP.

## Why this Skill

- Asks for degree level, academic background, research subdirection, and delivery format in one conversational turn.
- Reuses answers from visible conversation history instead of asking the same question again.
- Runs CQVIP keyword and AI searches only after the proposal brief is complete.
- Deduplicates papers by DOI, provider ID, and normalized title.
- Never invents authors, titles, journals, publication years, or DOI values.
- Degrades safely when CQVIP is unavailable: non-citation sections may continue, while references remain explicitly unavailable.
- Uses only the Python standard library at runtime.

## Execution Boundary

```text
User conversation
      │
      ▼
runner.py / main.py
  collect requirements
  retrieve literature evidence
      │
      ▼  status=ready_to_write
Host Assistant
  write proposal prose
  create Markdown / Word / LaTeX / PDF when supported
```

`runner.py` does not contain a `write_proposal` action. It prepares structured requirements and literature evidence; the host Assistant performs the open-ended writing step according to `SKILL.md`.

## Requirements

- Python 3.10 or newer.
- A Jenius sandbox, or another host that can load `SKILL.md` and execute `runner.py`.
- Optional CQVIP API access for real-time literature retrieval.
- Outbound HTTPS access to `superapi.cqvip.com:443` when CQVIP is enabled.

No third-party Python package is required for the Skill runtime.

## Quick Start

Clone this repository from GitHub, enter its directory, and run a first-turn example:

```bash
python runner.py --input examples/first-turn-request.json --pretty
```

The response has `status=needs_input` and contains four Assistant questions.

For a complete brief:

```bash
python runner.py --input examples/complete-request.json --pretty
```

Without a CQVIP key, the second command still returns `ready_to_write`, with `literature_evidence.status=unavailable` and no fabricated references.

## CQVIP Configuration

Provide the API key only through the runtime environment:

```bash
export CQVIP_API_KEY="your-key"
python runner.py --input examples/complete-request.json --pretty
```

PowerShell:

```powershell
$env:CQVIP_API_KEY = "your-key"
python runner.py --input examples/complete-request.json --pretty
```

Never put a real key in source code, JSON requests, logs, examples, ZIP files, issues, or pull requests. Copy `.env.example` only as a local reference; this Skill does not automatically load `.env` files.

## Install in Jenius

1. Download the ZIP attached to the latest GitHub Release, or build it locally.
2. Host the ZIP at a URL reachable by both Jenius and its sandbox.
3. Register the Skill URL through the Jenius custom Skill interface.
4. Select `thesis-proposal-writer` in the Agent configuration.
5. Configure `CQVIP_API_KEY` in the sandbox service, not in the chat request.
6. Allow outbound HTTPS access to `superapi.cqvip.com:443`.

The release ZIP places `SKILL.md`, `runner.py`, `main.py`, `core/`, and `references/` at its root. Archive paths always use `/`, so Linux sandboxes extract them correctly.

## Development

Run all offline tests:

```bash
python -m unittest discover -s tests -v
```

Run the opt-in live CQVIP test:

```bash
CQVIP_LIVE_TEST=1 CQVIP_API_KEY="your-key" \
  python -m unittest tests.test_live_api -v
```

Build a cross-platform release archive:

```bash
python scripts/package_skill.py --output-dir dist
```

The packager rejects hardcoded CQVIP keys, verifies required files, enforces POSIX ZIP entry names, and writes a SHA-256 checksum.

## Repository Layout

```text
.
├── SKILL.md                 Agent-facing workflow and constraints
├── main.py                  Proposal preparation workflow
├── runner.py                JSON CLI entrypoint
├── core/                    CQVIP client and normalization
├── references/              Proposal and API references loaded on demand
├── examples/                Safe example inputs and outputs
├── tests/                   Offline and opt-in live tests
├── scripts/                 Cross-platform packaging utilities
└── .github/workflows/       CI and release automation
```

See [Architecture](docs/architecture.md), [Troubleshooting](docs/troubleshooting.md), and [Privacy and Academic Integrity](docs/privacy-and-academic-integrity.md) for operational details.

Maintainers preparing the public repository should also apply the suggested [GitHub repository settings](docs/repository-settings.md).

## Limitations

- CQVIP results are metadata and abstracts, not proof that the full paper was read.
- Search availability depends on the sandbox network, CQVIP account permissions, quota, and provider uptime.
- Generated academic text requires human review and must comply with institutional rules.
- Word/PDF creation depends on document tools available in the host sandbox.

## Contributing

Bug reports and focused pull requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) before submitting changes.

## License

Released under the [MIT License](LICENSE). API access and literature metadata remain subject to CQVIP's own terms and the user's subscription permissions.
