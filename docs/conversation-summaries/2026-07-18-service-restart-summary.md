# Service Restart Conversation Summary

## Request

Stop all background processes that own listening TCP ports, then reopen the project website.

## Actions

- Enumerated listening TCP process IDs and force-stopped every terminable owner process.
- System-protected service listeners remained because they cannot be terminated at the current privilege level.
- Started the project with `start.ps1`; it selected API port 8000 and web port 3002.

## Verification

- `http://127.0.0.1:8000/health` returned HTTP 200.
- `http://127.0.0.1:3002/login` returned HTTP 200.
