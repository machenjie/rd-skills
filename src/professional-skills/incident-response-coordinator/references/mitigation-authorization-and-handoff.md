# Mitigation Authorization and Handoff

**Load when:** An active incident needs mitigation comparison, operator authorization boundaries, recovery verification, closure criteria, or transfer of command.

**Do not load when:** The task is only causal diagnosis, a release or rollback approval decision, reliability design, or post-incident documentation.

**Required by:** `analysis-agent`

**Required output:** `failure-decision`, `decision-record`, `residual-risk`
## Mitigation and Handoff Decision

Select a mitigation and handoff contract that supports recovery without converting coordination into authorization or execution.
## Mitigation Coordination Record

| Field | Required content |
|---|---|
| Objective | Impact to reduce, expected recovery state, and deadline |
| Authority | Governing policy, approval owner, authorized operator, and prohibited actions |
| Candidate | Proposed change, target, assumptions, dependencies, and alternatives |
| Risk | Blast radius, failure modes, sensitive scope, and concurrent-change conflicts |
| Recovery | Reversibility, recovery path, recovery owner, and unknown-outcome treatment |
| Control | Preconditions, stop conditions, observation window, and abort signal |
| Verification | Expected signal, independent check, evidence owner, and success threshold |
| Change ledger | Accepted action, start and end time, operator, outcome, and reconciliation state |
| Residual risk | Temporary control, unresolved impact, expiry, owner, and next decision |

## Handoff Record

| Field | Required content |
|---|---|
| Transfer | Outgoing commander, incoming commander, authority owner, and effective time |
| Current state | Impact, severity, service state, active mitigation, and latest verified evidence |
| Active work | Workstream, owner, dependency, authority boundary, and next checkpoint |
| Open decisions | Options, evidence, deadline, decision owner, and escalation path |
| Communications | Last message, approved facts, audience, owner, and next update |
| Acceptance | Briefing completed, questions resolved, records accessible, and command acknowledged |

## Decision Rules

- Keep mitigations in proposed state until explicit authorization is recorded.
- Require a named operator for accepted actions.
- Reject an action with no bounded target or recovery path.
- Stop concurrent changes that cannot be distinguished in the evidence.
- Define the verification signal before execution.
- Treat an unknown result as an active incident condition.
- Separate service recovery from root-cause confidence.
- Keep temporary controls open until an owner and expiry are recorded.
- Transfer command only after a complete briefing and acknowledgement.
- Close only when recovery evidence and residual ownership are explicit.

## Primary Sources

- [NIST SP 800-61 Rev. 3, Incident Response Recommendations and Considerations for Cybersecurity Risk Management](https://csrc.nist.gov/pubs/sp/800/61/r3/final), published April 2025 and accessed 2026-07-26.
- [CISA Federal Government Cybersecurity Incident and Vulnerability Response Playbooks](https://www.cisa.gov/sites/default/files/2023-02/Federal_Government_Cybersecurity_Incident_and_Vulnerability_Response_Playbooks_508C.pdf), accessed 2026-07-26.
- [Google SRE: Managing Incidents](https://sre.google/sre-book/managing-incidents/), accessed 2026-07-26.
- [FEMA ICS 200: Establishment and Transfer of Command](https://emilms.fema.gov/is_0200c/content/297.html), accessed 2026-07-26.

## Proof Limits

The coordination record proves proposed controls, recorded authorization, observed signals, and accepted handoff. It does not itself authorize an action, prove production execution, establish legal authority, or demonstrate durable recovery beyond the captured verification window.
