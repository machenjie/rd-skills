## Benchmark Task

You are working inside an isolated copy of a starter repository.

Read the task below, modify only the candidate repository, and leave a concise
final answer that includes:

- files changed;
- this compact trace block when the task changes behavior, tests, structure, or
  operational evidence:

```text
Process Trace:
PDD: problem + acceptance + constraints
DDD: domain ownership + invariants + side-effect boundary
SDD: modules + public API + error/logging decision
TDD: tests/validation mapping
Validation:
Residual Risk:
```

- the compact Process Trace parser supports a bounded YAML-like subset:
  `key: value`, `key:` with indented child keys, nested `- item` lists, and
  simple scalar booleans. Do not use anchors, flow collections, folded or block
  scalars, multi-document YAML, or deeply nested structures. Prefer a fenced
  JSON `process_trace` block when exact structure matters;
- validation commands run and their result;
- reuse or placement evidence when relevant;
- residual risk.

Preserve `setup.sh` and benchmark harness entrypoints. Do not delete, move,
chmod-break, or rewrite `setup.sh` unless the task explicitly requires it. If
`setup.sh` must change, keep it compatible with `CHANGEFORGE_CODEGEN_ROOT` and
runnable from the candidate root. Do not rely on fixed-depth parent traversal to
locate the repository root. Do not add external network dependencies. Do not add
package dependencies unless explicitly required; prefer the standard library and
existing files. If a dependency is unavoidable, document why and keep setup
deterministic. Do not write into `HOME` or `CODEX_HOME`. Before the final
response, run or reason through setup and report exact validation commands and
results. Keep process notes compact: PDD acceptance criteria, DDD invariants,
SDD public API/module/failure-mode/logging choices, and TDD validation commands
should map to the implemented change and tests.

{{TASK_PROMPT}}
