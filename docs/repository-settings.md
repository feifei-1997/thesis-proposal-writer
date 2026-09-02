# Recommended GitHub Repository Settings

These settings are configured in GitHub after the first push and cannot be expressed entirely through repository files.

## Name and Description

Suggested repository name:

```text
thesis-proposal-writer
```

Suggested description:

```text
Portable Agent Skill for conversational thesis proposal writing with CQVIP literature retrieval.
```

## Topics

```text
ai-agent
agent-skill
skill-md
agent-tools
thesis-writing
academic-writing
literature-search
cqvip
python
chinese-nlp
research-assistant
```

## Features

- Enable Issues and Discussions.
- Enable private vulnerability reporting.
- Keep secret scanning and push protection enabled.
- Use `main` as the default branch and require the `CI` workflow before merging.
- Add a `1280 × 640` social preview that shows the flow from four-question intake to literature evidence and proposal output.

## First Release

1. Replace the generic copyright holder in `LICENSE` if desired.
2. Verify that the former test API key has been revoked and rotated.
3. Push the clean repository and confirm CI passes.
4. Add repository secret `CQVIP_API_KEY` only if maintainers need the manual live test.
5. Create and push tag `v1.0.0`.
6. Confirm the Release contains both the ZIP and `.sha256` file.
7. Test the Release ZIP in a clean Linux sandbox before announcing it.
