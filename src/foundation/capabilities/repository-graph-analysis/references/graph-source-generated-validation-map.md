# Graph Source Generated Validation Map

Use this reference when repository graph evidence must separate editable source from generated outputs and map changed paths to validation, report, package, install, rollback, or handoff obligations.

## Source And Generated Boundary

| Boundary | Include | Closure requirement |
| --- | --- | --- |
| Editable source | Skill body, source module, registry source, script source, template source, hook runtime source. | Edit here first and cite direct source inspection. |
| Generated output | `dist/`, generated docs, compiled runtime artifacts, copied installs, generated clients, generated reports. | Identify source, generator, profile, and validator before relying on output. |
| Report/eval artifact | Professionalism report, audit report, benchmark output, routing output, coverage matrix. | Treat as generated evidence that becomes stale after material source or validator changes. |
| Package/install output | Zip, installed skill folder, runtime copy, release bundle. | Validate build/install path and do not treat copied output as source truth. |
| Unknown boundary | File or artifact lacks source, generator, owner, or policy. | Block edit/closure or route to owner until source truth is established. |

## Changed Path To Validation Mapping

For each changed path, record:

- `path`: source, reference, registry, hook runtime, test, report, generated output, package, or install artifact.
- `source_of_truth`: editable source path or unknown.
- `generated_outputs`: outputs that must be rebuilt or validated.
- `graph_edges`: symbol, import, call/reference, test, ownership, generated, report, memory, or trajectory edges used.
- `validator_candidates`: direct test, eval, benchmark, build profile, install check, link checker, or manual review.
- `selected_validator`: command or review gate chosen by `validation-broker`.
- `not_run_or_missing`: gap, reason, residual risk, and owner.
- `rollback_note`: file-level revert, rebuild, report regeneration, package cleanup, or owner handoff.

## Validation Selection Rules

1. Source-only skill or capability edits require skill validators, body-link checks, content-size checks, audit, professionalism eval, and any domain-specific regression named by the repository.
2. Registry or routing changes require registry validation, routing eval, professional routing coverage, and stage routing architecture checks.
3. Hook runtime source changes require hook validation, unit tests, build profiles, runtime reference links, and installation validation.
4. Generated outputs require the source build command and post-build reference/install validation.
5. Missing direct test edges require explicit residual risk and a broader validator or owner review.

## Output Fragment

```yaml
changed_graph_to_validation_map:
  - path: ""
    source_of_truth: ""
    generated_outputs: []
    graph_edges: []
    validator_candidates: []
    selected_validator: ""
    not_run_or_missing: ""
    rollback_note: ""
handoff:
  closure_decision: "ready|partial|blocked|not_verified"
  owner_reviewer_route: ""
  validation_limits: []
  rollback_note: ""
  next_gate: ""
```

## Anti-Bloat Guard

Include only graph nodes that change the edit target, dependency direction, affected validation, owner/reviewer route, generated artifact freshness, rollback, or closure language. Exclude broad neighborhoods with a reason rather than expanding the context pack.
