# Contributing

Thank you for improving Thesis Proposal Writer.

## Development Setup

Python 3.10 or newer is required. Runtime code has no third-party dependencies.

```bash
python -m unittest discover -s tests -v
python scripts/package_skill.py --output-dir dist
```

Offline tests must not contact CQVIP. The live test is opt-in and requires both `CQVIP_LIVE_TEST=1` and a repository-local `CQVIP_API_KEY` environment variable.

## Pull Requests

- Keep `SKILL.md` focused on Agent behavior; put installation and contributor guidance in repository documentation.
- Add tests for observable workflow behavior, not exact prose formatting.
- Keep the release package dependency-free unless a dependency is essential and documented.
- Verify the ZIP on both Windows and Linux when changing packaging logic.
- Never commit real API keys, private endpoints, proprietary paper content, or user research data.
- Update `CHANGELOG.md` for user-visible changes.

## Issues

Include the operating system, Python version, Jenius/sandbox version, sanitized runner input, and structured error code. Remove credentials and personal data before posting.
