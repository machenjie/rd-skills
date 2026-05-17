# Example Output

## Mobile Domain Findings
- Blocking: offline edits need a conflict policy before release because server updates can arrive while the app is suspended.
- Lifecycle requirement: on resume, refresh authorization, replay unsent operations idempotently, and recover the intended screen after notification tap.
- Release constraint: backend must support the current and previous major app versions during phased rollout.

## Verification
- Device tests for Android and iOS permission denial, notification tap routing, offline create/update, and cold start.
- Regression tests for mixed-version API compatibility.
- Release monitoring for crash-free sessions, sync failures, ANR, and notification open errors.
