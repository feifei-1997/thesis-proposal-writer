# Troubleshooting

## `ModuleNotFoundError: No module named 'core'`

Confirm that the archive contains `core/cqvip_client.py`, not a literal filename such as `core\cqvip_client.py`:

```bash
python -m zipfile -l thesis-proposal-writer-1.0.0.zip
```

Build releases with `python scripts/package_skill.py`; it always writes POSIX ZIP paths.

## `CQVIP_NOT_CONFIGURED`

Set `CQVIP_API_KEY` in the process or container that executes `runner.py`. Setting it only in the Chatchat API service does not help when the Skill runs in a separate sandbox.

## `CQVIP_NETWORK_ERROR`

The sandbox must resolve and connect to `superapi.cqvip.com:443`:

```bash
python -c "import socket; print(socket.getaddrinfo('superapi.cqvip.com', 443))"
python -c "import socket,ssl; s=socket.create_connection(('superapi.cqvip.com',443),10); t=ssl.create_default_context().wrap_socket(s,server_hostname='superapi.cqvip.com'); print(t.version()); t.close()"
```

Common causes are disabled outbound networking, DNS failure, a missing HTTPS proxy, a blocked firewall rule, or missing CA certificates.

## `CQVIP_HTTP_ERROR` with 401 or 403

The network path is working. Check API key validity, endpoint permissions, subscription status, and any provider-side source-IP allowlist.

## `ready_to_write` with unavailable literature

This is intentional graceful degradation. The host Assistant may draft sections that do not depend on citations, but must state that live retrieval was unavailable and must not invent references.

## `write_proposal` is not a supported action

The runner prepares requirements and literature evidence. The host Assistant writes prose after receiving `ready_to_write`; Word/PDF conversion uses document tools supplied by the host sandbox.

## Chinese text appears as `????` in PowerShell

Prefer `--input` with a UTF-8 JSON file instead of piping Chinese text through older Windows PowerShell versions:

```powershell
python runner.py --input examples\complete-request.json --pretty
```
