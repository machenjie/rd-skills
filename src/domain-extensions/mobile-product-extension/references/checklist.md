# Mobile Product Extension Checklist

- Offline, retry, sync, conflict, and local persistence behavior are defined.
- App lifecycle covers cold start, warm start, resume, background, suspended, terminated, logout, and session expiry.
- Push notifications define permission request timing, payload, delivery assumptions, tap route, stale handling, and quiet hours if relevant.
- Device permissions cover allowed, denied, limited, revoked, and settings-change flows.
- Privacy prompts and data collection match platform disclosure requirements.
- Android and iOS behavior differences are explicit, including OS version limits and device capability gaps.
- Background execution behavior accounts for OS limits, battery settings, and retry windows.
- Deep links and universal/app links handle installed, not installed, unauthorized, and stale targets.
- Release plan covers phased rollout, rollback limits, forced or optional upgrade, and mixed client/server compatibility.
- Monitoring covers crash-free rate, ANR, latency, battery impact, notification delivery, sync failures, and app version.
