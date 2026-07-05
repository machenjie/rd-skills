## Benchmark Task

You are working inside an isolated copy of a starter repository.

Read the task below, modify only the candidate repository, and leave a concise
final answer that includes:

- files changed;
- this field-level process trace when the task changes behavior, tests,
  structure, or operational evidence:

```json
{
  "process_trace": {
    "pdd": {
      "problem": "specific problem solved",
      "acceptance_criteria": ["observable acceptance criterion"],
      "constraints": ["harness or dependency constraint"],
      "validation_signal": ["exact command or check"]
    },
    "ddd": {
      "domain_terms": ["domain term"],
      "invariants": ["business or system invariant"],
      "ownership_decision": ["module or service that owns the rule"],
      "side_effect_boundaries": ["where side effects are allowed or forbidden"]
    },
    "sdd": {
      "modules": ["file, module, or component changed"],
      "public_api": ["public function, endpoint, command, or UI behavior"],
      "error_contract": ["expected error or failure behavior"],
      "failure_modes": ["failure mode covered"],
      "logging_decision": {"needed": false, "rationale": "why logs are or are not required"},
      "design_decision_points": [],
      "no_design_choice_rationale": "specific code fact, repository convention, prompt constraint, or reuse evidence showing no material choice exists",
      "assumption_policy": "block_when_wrong_answer_changes_contract_architecture_data_security_acceptance_or_user_visible_behavior"
    },
    "tdd": {
      "acceptance_to_tests": {"observable acceptance criterion": ["exact command or test"]},
      "invariant_to_tests_or_code": {"business or system invariant": ["exact command, test, or code path"]},
      "public_api_to_tests": {"public API or behavior": ["exact command or test"]},
      "failure_mode_tests": ["failure mode -> exact command or test"],
      "validation_commands": ["exact command and result"]
    }
  }
}
```

- the compact Process Trace parser supports a bounded YAML-like subset:
  `key: value`, `key:` with indented child keys, nested `- item` lists, and
  simple scalar booleans. Do not use anchors, flow collections, folded or block
  scalars, multi-document YAML, or deeply nested structures. Prefer a fenced
  JSON `process_trace` block when exact structure matters. Do not leave generic
  placeholders such as "problem + acceptance + constraints"; every required
  field must map to this specific candidate change;
- strict traceability is required: every exact string in
  `pdd.acceptance_criteria` must be an exact key in `tdd.acceptance_to_tests`,
  every exact string in `ddd.invariants` must be an exact key in
  `tdd.invariant_to_tests_or_code`, every exact string in `sdd.public_api`
  must be an exact key in `tdd.public_api_to_tests`, and each
  `sdd.error_contract` or `sdd.failure_modes` item must be mapped by
  `tdd.failure_mode_tests`. If `sdd.logging_decision.needed` is `false`, the
  rationale must name the validation, test, public-behavior, metric, or trace
  evidence that replaces runtime logging. If `sdd.logging_decision.needed` is
  `true`, include non-empty `log_types`, `placement`, `events`, `levels`,
  `fields`, `redaction`, `correlation`, `cardinality_controls`, and
  `tests_or_validation` fields, or map equivalent checks in
  `tdd.logging_or_security_tests`. Event names must be specific operational
  events, not generic log descriptions. When `log_types` includes both `audit`
  and `diagnostic`, state separate sink and retention rationale explicitly;
- SDD must include `design_decision_points` and `assumption_policy`. Required,
  blocking, material, or high-risk choices need user-visible `options`,
  `recommended_option`, `user_choice_status`, `why_user_choice_is_needed`,
  boolean `blocking`, `resolution_evidence`, and `residual_risk`;
  required/blocking/material/high-risk choices need at least two options, each
  with `label`, `summary`, and `pros` or `cons`. `blocking` must be true or
  false, not a string. `recommended_option` is the recommendation, not user
  selection; unresolved required/blocking choices cannot close as SDD present.
  Resolved material choices require `resolution_evidence`;
  material `not_required` choices require prompt, fixture, explicit-user,
  repository, or reuse evidence. If interactive user choice is unavailable,
  state why the prompt/fixture already decides, why the choice is a safe
  low-risk assumption, or why implementation should be blocked or degraded. Do
  not write generic "no choice needed"; no-choice rationale must cite concrete
  code facts, repository convention, prompt constraints, or reuse evidence;
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
