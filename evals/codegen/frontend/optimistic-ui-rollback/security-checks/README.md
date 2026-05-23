# Security Checks

## Threat Surface

The UI handles task identifiers, project membership, and server conflict
messages. The main risks are trusting optimistic state as authority, leaking
forbidden task details, and allowing duplicate side effect requests.

## Required Checks

- Treat server success or conflict response as authoritative.
- Render server error text safely as text.
- Avoid exposing locked project details beyond approved response content.
- Prevent duplicate archive requests for the same task while pending.
- Do not persist rollback snapshots beyond the active recovery window.

## Rejection Cases

- Any solution keeps the task archived after the server rejects the request.
- Any solution renders server error content as raw HTML.
- Any solution sends multiple archive requests from rapid repeated clicks.