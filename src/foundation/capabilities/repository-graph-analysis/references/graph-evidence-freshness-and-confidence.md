# Graph Evidence Freshness And Confidence

Use this reference when repository graph facts, reports, memory signals, or execution trajectory evidence may be stale, low-confidence, conflicting, or selector-only. The `SKILL.md` body owns routing; this reference defines the accepted evidence states and downgrade rules.

## Evidence States

| State | Required basis | Professional use | Closure limit |
| --- | --- | --- | --- |
| Current high confidence | Extractor/source and direct source inspection agree after the latest material edit. | May support planning, validation mapping, and handoff. | Still does not replace behavior review. |
| Current medium confidence | Graph is fresh, but source semantics, dynamic references, or ownership need inspection. | May select files, tests, and reviewers. | Must not prove behavior alone. |
| Low confidence | Broad search, dynamic path, generated edge, incomplete metadata, or weak owner hint. | Selector for further inspection. | Cannot support closure. |
| Stale | Selected source, generated output, registry, report, dependency manifest, validation input, or memory signal changed after graph creation. | Refresh or direct-source fallback. | Cannot be cited as current proof. |
| Conflict | Graph, source, report, ownership, or generated edge disagree. | Route to source inspection or owner review. | Cannot choose the convenient fact silently. |
| Missing | Expected edge is absent, such as no test edge or no source for generated output. | Residual risk and validation broker input. | Absence is not proof of safety. |

## Freshness Checks

1. Compare graph/report creation order with final material edits, generated outputs, registry changes, dependency manifests, validation commands, and memory/trajectory signals.
2. Treat a graph as stale when any selected source, generated artifact, report, dependency manifest, or registry entry changed after the graph was built.
3. Prefer direct-source reread when graph refresh is not available within the turn.
4. Preserve relative-order evidence when exact timestamps or hashes are unavailable; do not invent precision.
5. Re-check validation freshness after the final material edit before handoff.

## Confidence Downgrade Rules

- Downgrade to selector-only when a graph edge comes only from broad text search, generated output, dynamic import, dynamic registry use, or incomplete metadata.
- Downgrade when memory or trajectory signals identify prior fragility but current source has not been inspected.
- Downgrade when generated artifacts lack a source file, generator command, runtime profile, or validator.
- Downgrade when an ownership or source-of-truth edge conflicts with local conventions, registry evidence, or source comments.
- Mark unknown-consumer risk when no caller edge is found but dynamic consumers, scripts, docs, jobs, packages, or generated clients were not inspected.

## Evidence Limit Template

```yaml
evidence_limits:
  what_evidence_proves:
    - accepted graph facts and direct-source checks
    - changed-path validator candidates
    - source/generated boundary that was inspected
  what_evidence_does_not_prove:
    - runtime behavior not read in source
    - dynamic consumers outside searched boundaries
    - omitted low-confidence graph areas
    - stale reports or validators
  residual_risk:
    - stale facts
    - missing edges
    - conflicts
    - unknown consumers
```

## Handoff Rules

1. Name accepted, stale, rejected, missing, and conflicting graph facts separately.
2. State whether each graph fact is planning evidence, validation evidence, review evidence, or closure evidence.
3. Attach source inspection evidence for behavior-critical, ownership-critical, or source-of-truth claims.
4. Map any stale, missing, or conflicting fact to a validator, owner review, direct-source fallback, or residual risk.
5. Do not use stale memory, trajectory, or report evidence as proof after later material edits.
