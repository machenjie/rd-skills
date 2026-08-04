# Threat Modeling Benchmarks And Patterns

Load this reference when current graph evidence leaves multiple abuse-path, impact, control-placement, bypass, validation, detection, or residual-risk patterns viable. Do not load it to copy a framework taxonomy or fixed control catalog.

## Abuse-Path Decision Patterns

| Decision | Compare | Required proof |
| --- | --- | --- |
| Security delta | Changed asset or authority, entry point, trust transition, data/control flow, dependency, and downstream effect | Current graph edge, change evidence, owner, and explicit unknown or out-of-scope edges |
| Actor capability | External, legitimate-user, insider, service, partner, or compromised-component behavior reachable in the current graph | Access, knowledge, timing, control, prerequisite, and denied or constrained capability evidence |
| Path reachability | Source, attacker-controlled or stale value, transformations, policy/parser decisions, transport/storage, sink, and effect | Source-to-effect trace, evidenced assumptions, alternate branches, and reachability check |
| Protected outcome and impact | Confidentiality, integrity, availability, safety, financial, privacy, tenant, or authority consequence | Current exposure, affected subjects or systems, reversibility, propagation, and blast-radius evidence |
| Control placement | Prevention, containment, detection, recovery, or combined controls at candidate graph edges | Protected outcome, intercepted edge, authority, owner, failure behavior, compatibility, and bypass scan |
| Validation and detection | Abuse/negative test, source/config/policy proof, monitoring/audit signal, or controlled review appropriate to the path | Final-edit freshness, expected failure or signal, safe fields, owner, and proof limit |
| Residual treatment | Repair, containment, compensating evidence, release condition, accepted consequence, or unresolved scope | Accountable owner, rationale, decision authority, reopen trigger, and downstream consequence |

## Control Selection Guardrails

- Select a control after naming the reachable edge and protected outcome; the same threat label can require different placement or no additional mechanism in different systems.
- Trace control failure, degraded or unavailable authority, partial rollout, alternate entry points, retries, caches, generated artifacts, operator paths, and downstream copies when they can bypass or weaken the selected edge.
- Route authenticated-subject authority and handoff to authentication-authorization. authentication-security owns credential/session/token lifecycle depth, and permission-boundary-modeling owns permission-matrix depth. input-validation or web-security owns hostile-input sink depth. secret-configuration-security owns secret lifecycle depth when the corresponding path is triggered.

## Proof Limits

Repository inspection, tests, scans, and design artifacts cover their named graph, environment, data, and time boundary. They do not establish undiscovered routes, production policy or configuration, external consumers, live attacker behavior, detection latency, or future exposure unless those surfaces are independently verified.
