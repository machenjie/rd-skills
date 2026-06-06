# CI/CD Pipeline Benchmarks — Gate Decision Detail

Deep reference for the `## Industry Benchmarks` section in the `ci-cd` capability. The body
carries the fail-fast stage table, the deployment-strategy table, and the supply-chain
hardening table; this file carries the illustrative gate-blocking decision tree. The
decision-critical rule ("Required checks block promotion … except via a named, audited
emergency-override") lives in the capability's Non-Negotiable Rules. This reference is loaded
in the `dev` profile and by skill authors.

## Decision Tree: Should This Gate Block?

```
Is this a security finding (SAST HIGH+, secrets detected, CVE CRITICAL in runtime image)?
└─ Yes → BLOCK (no bypasses except documented emergency exception with CISO sign-off).

Is this a failing unit / integration / regression test?
├─ Flaky (known) → Quarantine track; still BLOCK on mandatory suite.
└─ New failure → BLOCK. Fix or revert.

Is this a MEDIUM dependency vulnerability in a dev-only package?
└─ Warn only; track in vulnerability backlog; SLA = 30 days.

Is this a build-time lint / format failure?
└─ BLOCK in CI; developer-class fix (< 15 min).

Is this a production deploy to regulated environment?
└─ Require: change-ticket, approval(s), deploy window, rollback plan, post-deploy test.
```
