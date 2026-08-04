# Command Cadence and Decision Log

**Load when:** An active incident needs a commander, explicit roles, a reporting cadence, bounded workstreams, or one shared evidence and decision record.

**Do not load when:** One owner is performing ordinary diagnosis, the work is a reliability design review, or the incident is already closed and only documentation remains.

**Required by:** `analysis-agent`

**Required output:** `decision-record`, `proof-limit`, `residual-risk`

## Command Contract Decision

Select a command, cadence, and logging contract that keeps the active responder set aligned to the same current incident state.

## Incident Command Record

| Field | Required content |
|---|---|
| Declaration | Incident identifier, trigger, current status, affected scope, and declaration time |
| Severity | Policy basis, observed impact, uncertainty, owner, and next review point |
| Command | Commander, authority owner, technical lead, mitigation operator, communications lead, and scribe |
| Cadence | Coordination channel, update frequency, next checkpoint, and escalation channel |
| Workstreams | Bounded objective, owner, action scope, dependencies, authority boundary, and reporting time |
| Timeline | Event time, observation time, record time, source, freshness, and confidence |
| Decisions | Decision, alternatives, rationale, authority, owner, timestamp, and review condition |
| Actions | Proposed or accepted state, operator, target, expected signal, actual outcome, and reconciliation state |
| Communications | Audience, approved facts, uncertainty, impact, owner, publish time, and next update |

## Decision Rules

- Use the current incident policy to assign severity.
- Mark unverified scope, timing, and impact as provisional.
- Assign one accountable owner to each workstream.
- Keep event time distinct from observation and recording time.
- Link each decision to the evidence available at that time.
- Log an action before an authorized operator performs it.
- Reconcile completed, failed, cancelled, and superseded actions.
- Publish status from the shared record.
- Record dissent and unresolved uncertainty.
- Preserve the next checkpoint during commander handoff.

## Primary Sources

- [NIST SP 800-61 Rev. 3, Incident Response Recommendations and Considerations for Cybersecurity Risk Management](https://csrc.nist.gov/pubs/sp/800/61/r3/final), published April 2025 and accessed 2026-07-26.
- [CISA Federal Government Cybersecurity Incident and Vulnerability Response Playbooks](https://www.cisa.gov/sites/default/files/2023-02/Federal_Government_Cybersecurity_Incident_and_Vulnerability_Response_Playbooks_508C.pdf), accessed 2026-07-26.
- [Google SRE Workbook: Incident Response](https://sre.google/workbook/incident-response/), accessed 2026-07-26.
- [Google SRE: Managing Incidents](https://sre.google/sre-book/managing-incidents/), accessed 2026-07-26.

## Proof Limits

The record proves what responders logged and what evidence they linked. It does not prove that a source was accurate, an operator had authority, an action occurred in production, or recovery was durable without independent verification.
