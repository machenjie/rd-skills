# Python Evidence Patterns

Use this reference when Python closure depends on repository graph, project memory, execution trajectory, validation freshness, type/runtime/dependency proof, tool permission boundaries, or changed-surface-to-validation mapping. Keep it as an evidence map; use `benchmarks-and-patterns.md` for deeper tooling and runtime pattern detail.

## Changed-Python-Surface-To-Validation Map

| Python claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Runtime boundary is validated | Boundary path, validator/schema/parser location, malformed fixture, and strict typecheck or runtime validation test | The inspected external input is parsed before trusted use | All producers, historic payloads, notebooks, or downstream consumers are covered |
| Async/resource path is safe | Blocking-call scan, timeout/cancellation behavior, context-manager review, lag/profile artifact or not-run owner | The inspected path avoids or bounds blocking calls and resource leaks | Production p99, every scheduler interleaving, or external SDK behavior is proven |
| Environment is reproducible | `pyproject.toml`, lockfile, frozen install command, import smoke test, and package metadata review | The selected environment can install and import deterministically | Future resolver behavior, optional extras, or target deployment image is covered |
| Fixtures and scripts are rerun-safe | Fixture scope/cleanup, randomized or ordering-sensitive test result, dry-run output, idempotency guard, rollback/redaction note | The inspected test or operational path has bounded state effects | Live production side effects or every suite ordering is proven |
| Security-sensitive Python idiom is safe | Deserialization/subprocess/SQL/path/logging path, sanitizer or safe API, hostile-input test, bandit/audit result or review | The named trust boundary has a reviewed mitigation | All attack variants, secrets in external systems, or deployment settings are covered |
| Prior evidence is still fresh | Current source/config/lock/generated paths, accepted/rejected memory, command/report path, and final-edit freshness | The prior claim still matches inspected current files | Later edits, hidden generated artifacts, or uninspected CI jobs remain covered |

## Evidence Quality Labels

- **Strong evidence**: current source/config/lock/test inspected, command or artifact named, exit code or review status recorded, final-edit freshness stated, and proof limits named.
- **Weak evidence**: type hints without runtime validator, old pytest/CI output, local virtualenv success, notebook output, generic style guide, or memory claim without current source.
- **Missing evidence**: no boundary validator, no invalid-input fixture, no lockfile/frozen install, no fixture cleanup proof, no dry-run/idempotency record, or no owner for not-run validation.
- **Invalid evidence**: `Any` as proof, unsafe deserializer on untrusted input, `shell=True` with user text, stale generated artifact, or inaccessible report.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Source reads, graph search, config/lockfile inspection, generated artifact review, and report review | Read-only local shell action; cite searched paths and avoid full output dumps. |
| ruff, mypy/pyright, pytest, coverage, bandit, pip-audit/osv, frozen install, and report refreshes | State-mutating only for caches, reports, build artifacts, virtualenvs, or fixtures; cite command, exit code, artifact path, and rollback/cleanup if relevant. |
| Notebook/data script, migration, subprocess automation, lockfile update, formatter/codemod, or package install | State-mutating development action; record dry-run, path/data scope, lockfile impact, redaction, rollback/compensation, and stop condition. |

## Handoff Evidence Shape

```yaml
python_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_python_surface_to_validation_map:
    - surface: ""
      risk: runtime_boundary | async_resource | packaging | fixture_script | security | freshness
      command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      freshness: fresh | stale | partial | not_run
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
