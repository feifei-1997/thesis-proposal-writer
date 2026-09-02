# Examples

- `first-turn-request.json`: an incomplete user request that triggers the four-question Assistant follow-up.
- `complete-request.json`: a complete proposal brief that proceeds to CQVIP retrieval and `ready_to_write`.
- `first-turn-response.json`: an abbreviated response showing the stable state and question fields.
- `ready-to-write-response.json`: an abbreviated no-key degradation response. With a configured key, `literature_evidence` may contain provider records and citations.

Response examples intentionally omit provider data and nonessential fields so they remain safe and readable. Treat the runner output, not these abbreviated fixtures, as the authoritative schema.
