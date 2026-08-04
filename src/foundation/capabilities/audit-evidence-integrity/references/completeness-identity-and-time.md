# Completeness, Identity, And Time

**Load when:** Audit coverage, actor/service fidelity, time uncertainty, ordering, correlation, or causality remains unresolved.

**Do not load when:** Work only selects record placement/schema, or current reconciliation proves complete attribution for the bounded audit question.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `decision-record`, `boundary-decision`, `proof-limit`

## One Decision

Select one coverage and attribution contract that reconstructs each critical outcome without overstating identity, time, order, or causality.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Coverage | Audit question, critical actions/outcomes, sources, window, expected records, and exclusions | Enabled logging is called complete |
| Record identity | Stable event identity, source, schema/version, tenant/resource scope, and duplicate meaning | Collector position becomes event identity |
| Human actor | Authoritative subject, real/effective actor, delegation, session/credential provenance, and assurance | Shared account is treated as attribution |
| Service actor | Workload identity, owning service, delegated caller, purpose, and acting authority | Service name hides the initiating principal |
| Time | Occurrence/commit/receipt values, clock source, offset, precision, sync health, and uncertainty | UTC formatting proves clock trust |
| Order | Per-source sequence, transaction/commit order, causal edge, and incomparable-event behavior | Wall-clock sort is called total order |
| Causality | Operation, request, parent, causation, correlation, retry, and effect identity | One correlation ID proves cause |
| Reconciliation | Expected-versus-observed counts/identities, lateness, duplicates, gaps, owner, and deadline | Missing records disappear from the denominator |

## Verification

- Exercise the critical success, denial, failure, retry, delegation, and administration paths in scope.
- Reconcile expected source facts against stored evidence across late, duplicate, and missing delivery.
- Skew, step, and restart clocks; reorder receipt; verify ordering claims supported by the observed clocks and receipt records.
- Replace actor, session, service, causation, and correlation values and require detection or safe uncertainty.

## Primary Sources

- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
- [NIST SP 800-92: Log Management](https://csrc.nist.gov/pubs/sp/800/92/final)
- [RFC 8633: Network Time Protocol Best Current Practices](https://www.rfc-editor.org/rfc/rfc8633.html)
- [AWS CloudTrail record contents](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-record-contents.html)
- [AWS CloudTrail event ordering](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-events.html)

Official sources were accessed on 2026-07-26.

## Proof Limits

Controls and platform fields do not prove configured coverage, identity truth, or source delivery. Time synchronization cannot establish a global total order; provider event semantics, coverage defaults, lateness, and identity fields are product- and event-type-specific.
