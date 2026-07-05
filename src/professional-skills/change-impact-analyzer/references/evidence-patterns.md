# Change Impact Evidence Patterns

Use this reference when impact closure depends on changed-surface-to-validation mapping, same-pattern scan proof, consumer evidence, rollback limits, graph/report freshness, or proof limits. Keep `SKILL.md` for selection and output rules; load this file only for concrete evidence closure.

## Evidence Map

- **Local fix scope:** record pattern signature, searched paths, command output or report, related occurrences, and local-only or broad-fix decision.
- **Contract or consumer impact:** record old/new shape, named consumers, compatibility class, generated-client or fixture effect, migration/deprecation note, and unverified consumer risk.
- **Data or stateful impact:** record mutated state, migration/backfill path, rollback or forward-fix evidence, old/new version skew, and release gate owner.
- **Security or permission impact:** record auth boundary, allowed and denied paths, audit/log expectation, sensitive data classification, and security gate handoff.
- **Docs/tests/release impact:** record affected tests, fixtures, docs, runbooks, changelog, CI/release artifacts, validator command, and stale evidence status.

## Validation Map

```yaml
changed_surface_to_validation_map:
  surface: ""
  impact_level: direct | indirect | downstream | none_with_rationale | unknown
  evidence:
    scan_or_command: ""
    inspected_boundaries: []
    result: ""
  proves: []
  does_not_prove: []
  owner_or_next_gate: ""
  residual_risk: ""
```

## Closure Checks

- Do not classify a surface as not impacted without named evidence or rationale.
- Treat dependency graphs, generated reports, and prior summaries as selectors until current source and validators confirm them.
- Separate static scan evidence from runtime traffic, production data, unknown consumer, and live rollback evidence.
- Re-run or downgrade validation when source, fixtures, docs, generated artifacts, or reports change after the scan.
