# Security Policy

## Supported Versions

Security fixes are provided for the latest `1.x` release.

## Reporting a Vulnerability

Use GitHub private vulnerability reporting when it is enabled for this repository. If it is unavailable, open an issue that contains no credential, token, private endpoint, unpublished paper, or personal research data, and ask the maintainer for a private contact channel.

Do not paste a CQVIP API key into an issue, discussion, pull request, screenshot, test fixture, log, or release archive. Revoke and rotate any credential that may have been exposed.

## Runtime Trust Boundary

- The Skill sends search queries to the configured CQVIP API endpoint.
- The host Assistant and sandbox control generated files and outbound network access.
- Users should inspect the release checksum and source before installing the Skill.
- API credentials must be injected through `CQVIP_API_KEY` at runtime.
