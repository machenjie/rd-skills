# Logging Output And Gates

Load only when assigned L3-L5 logging implementation or independent review needs mode-specific closure plus targeted proof for purpose, placement, fields/redaction/correlation, volume/sinks, or failure visibility.

## Do Not Load

Do not load when no logging behavior changes or when the root contract or compact checklist is sufficient. Use the selection-criteria reference only when a concrete decision needs its additional detail.

## Output Contract

Return exactly one mode closure, followed only by fields triggered by the selected logging risk:

1. **Task closure:**
   - Return the actual logging diff, post-edit validation, preserved behavior, proof limits, residual risk, and next independent-review owner.
   - Leave approval to an independent reviewer.
2. **Review closure:**
   - Return `Approved`, `Returned`, or `Blocked` with findings, reviewed and unreviewed changed files, and evidence limits.
   - Use `Blocked` for inaccessible required evidence, naming missing evidence, unblock condition, repair owner, and handoff.
   - Make no repair to the target.
3. **Purpose and signal choice:** State the operator, audit, security, or diagnostic question and whether a log is needed. A better existing signal leaves the selected metric, trace, test, alert, or no-new-signal outcome and current platform evidence explicit.
4. **Placement, level, and failure visibility:** When a log is selected, state the owning event boundary and the level chosen under current policy. From the changed lifecycle, name the reachable failure states the diagnostic or audit purpose needs to distinguish, and omit unobserved states from the claim. For operational response, state the operator action; for audit evidence, state its consumer and meaning instead.
5. **Fields, redaction, and correlation:** When a log is selected, state its purpose-required fields, their source, and allowed shape. Classified data carries omission or transformation evidence, while cross-boundary linkage carries the selected correlation outcome.
6. **Volume, cardinality, retention, and sinks:** When event rate or value space creates material volume/cardinality risk, state assumptions, cost/noise impact, and the selected sampling/aggregation/rate control. Separately, when classification or platform policy changes retention, access, or sink handling, state the selected boundary and owner.
7. **Evidence limits and next owner:** Tie tests, captured events, schema/redaction checks, logger configuration, sink evidence, or volume measurements to the decision they support. Name unverified production configuration/traffic, downstream processors, unusual framework behavior, and residual leakage or diagnosability risk.

## Quality Gate

1. Require a log only for a named event-record question that existing metrics, traces, tests, alerts, or signals cannot answer, excluding generic-visibility rationale.
2. When logging is selected, require one level and operator meaning supported by current policy and failure lifecycle. Additional levels and lifecycle events remain conditional on reachable, decision-relevant validation, retry, fallback, degradation, and terminal states.
3. After a diagnostic or audit purpose is selected for a log, include the stable fields needed to answer it and omit unneeded fields. Operation, outcome, actor/resource, duration, error category, version, or environment are candidates selected from current schemas and operator questions, not a universal template.
4. When a candidate field contains secret, credential, sensitive payload, or classified personal data, require omission or tested transformation consistent with policy. Allowlisting, redaction, hashing, tokenization, or access-controlled audit storage are candidates selected from data use and re-identification risk.
5. When events cross a boundary and linkage is needed, require a stable correlation outcome through a boundary-supported identifier without requiring every identifier or exposing raw identity values.
6. When frequency or field value-space can create material cost, noise, performance, or cardinality risk, require bounded evidence and a control outcome. Sampling, aggregation, rate limiting, lower level, metric conversion, retention change, or no log are candidates selected from measured/platform constraints.
7. When current policy assigns different retention, access, integrity, or sink requirements to audit, security, diagnostic, or access logs, state the selected separation and owner. Any mandate for every sink or fixed retention requires classification or policy evidence.
8. Scope completion to fresh evidence: task validation follows the final material edit, while review remains read-only. Tests and local capture do not prove production sink configuration, real traffic volume, retention enforcement, or downstream redaction; name residual risk and next owner.
