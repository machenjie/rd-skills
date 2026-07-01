# Stage Evidence Freshness

Use this reference when stage selection or handoff depends on repository graph, project memory, prior validation, generated reports, execution trajectory, repair/re-review order, or validation freshness.

## Freshness Classes

- **Current:** source, registry, reference, report, generated artifact, package, install output, command, or review evidence produced after the latest material edit.
- **Selector-only:** graph, memory, prior report, or trajectory evidence that can choose the next file, command, validator, or reviewer but cannot prove stage closure.
- **Stale:** evidence that predates final material edits or a changed stage, route, registry, generated artifact, validator, package, install output, or repair.
- **Rejected:** evidence contradicted by current source, fresh validator output, stage manifest, or reviewer finding.

## Coupling Checks

- **Repository graph:** confirm ownership, callers, tests, configs, generated artifacts, and source/dist boundary before selecting implementation, review, testing, or release stage evidence.
- **Project memory:** accept only claims with a current-source confirmation; otherwise mark them selector-only, stale, or rejected.
- **Execution trajectory:** compare command order, failed attempts, repairs, and re-review state before advancing the stage.
- **Validation freshness:** rerun or downgrade validation whenever source, registry, reference, generated report, package, install output, or stage route changes after the evidence was produced.

## Stage Handoff Record

Include current stage, next stage, selected and skipped capabilities, accepted/rejected graph or memory claims, trajectory order, final validation command and exit code, what the evidence proves, what it does not prove, rollback note, residual risk owner, and next gate.
