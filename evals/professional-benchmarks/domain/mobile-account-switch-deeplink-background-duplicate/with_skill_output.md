# Mobile Product Review

Primary Professional Skill: `installed-client-change-builder`
Selected Domain Skill: `android-platform-extension`

## Hidden risks

- account switch can expose prior-account cache files keys queued work or local rows
- an unverified deep link can act with stale tenant authority
- background retry after process recreation can duplicate a committed effect

## Required evidence

- account-switch isolation test across cache files keys rows and queue
- deep-link association authorization and stale-session negative tests
- process-death duplicate-dispatch recovery test

## Handoff

- mobile lifecycle and authority contract
- storage cleanup deep-link and background idempotency controls
- user-visible recovery proof limits and residual owner

Bind every persisted object and pending effect to the authenticated account, clear or isolate them before the next account becomes active, re-authorize deep-link intent against current state, and persist business identity across process death.
