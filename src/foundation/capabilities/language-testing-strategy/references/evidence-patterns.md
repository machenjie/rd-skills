# Language Testing Strategy Evidence Patterns

Use this reference when closure depends on mapping language/runtime risks to concrete validators, commands, fixtures, CI lanes, and report freshness. Keep `SKILL.md` for mode selection and output shape; load this file only for concrete evidence mapping.

## Runtime Risk To Evidence Map

| Runtime risk | Strong evidence | Weak or invalid evidence | Residual risk if absent |
| --- | --- | --- | --- |
| Dynamic boundary drift | Invalid/malformed fixture through runtime validator and negative assertion | Type hints, TS types, or schema file with no runtime test | Production accepts hostile or malformed input |
| Async cancellation or timeout | Test that cancels/deadlines the real boundary and proves cleanup | Happy-path async test only | Leaked task, stuck request, or stale resource |
| Shared mutable concurrency | Race detector, stress loop, loom/jcstress/model check, or scheduler permutation evidence | One deterministic test run | Data race, deadlock, duplicate side effect |
| Native/unsafe memory | ASan/UBSan/TSan/MSan, miri, fuzz, or crash corpus evidence | Ordinary unit test on valid input | UB, memory corruption, panic, or exploit path |
| Parser/deserializer boundary | Fuzz/property test with corpus/artifact and malformed cases | One golden fixture | Crash, injection, or resource exhaustion |
| Public/generated contract | Contract diff, generated compile, fixture replay, consumer verification | Local handler unit test only | SDK, mobile, partner, or event consumer breakage |
| AI-generated or mock-heavy tests | Public behavior assertion, real/fake/mock contract, mutation-style failure expectation | Call count, private helper, snapshot, or shape assertion | Tests pass while real behavior is wrong |
| Frontend accessibility/visual state | Playwright/Testing Library/axe/visual result at user-facing state boundary | CSS selector or DOM implementation detail | Keyboard/screen-reader or responsive regression |
| Coverage/mutation claim | Fresh coverage plus mutation score on critical module and relevant changed paths | Global coverage percentage or stale CI badge | High line coverage with weak assertions |

## Evidence Labels

- **Strong**: command run after final edit, working directory, exit code, relevant output, report/artifact path, risk covered, and what remains unproven.
- **Weak**: lint/typecheck/coverage-only, stale CI, one green happy-path test, snapshot-only result, graph-only changed-path map, or report without changed-path relevance.
- **Missing**: no command, no fixture, no runtime validator, no race/sanitizer/fuzz lane for a required risk, no contract consumer, or no fixture owner.
- **Invalid**: evidence from another language/runtime, a mock that cannot match the provider, tests that assert private implementation shape, or coverage reported after source/fixture/generated changes.

## Changed Path To Runtime Risk Map

For each changed path, branch, fixture, generated artifact, public contract, and runtime seam, record:

```yaml
language_validation_map:
  path: ""
  language_runtime: ""
  risk_mode: runtime_boundary | concurrency_async | native_memory | parser_fuzz | contract_generated | mock_fixture_ai | frontend_a11y_visual | coverage_mutation
  failure_to_catch: ""
  validation:
    command: ""
    cwd: ""
    exit_code: null
    artifact_or_report: ""
    proves: ""
    does_not_prove: ""
  fixture_or_mock_owner: ""
  freshness: fresh | stale | not_run
  residual_risk:
    owner: ""
    reason: ""
```

## Closure Checks

- Reject closure when runtime-sensitive changes cite only lint, typecheck, global coverage, or a single happy-path unit test.
- Reject closure when concurrency changes lack race/stress/cancellation proof or an explicit owner-accepted residual risk.
- Reject closure when native, unsafe, parser, deserializer, or hostile-input boundaries lack sanitizer, fuzz, property, or negative validation evidence.
- Reject closure when public/generated contracts changed without consumer, generated-client, or fixture replay evidence.
- Downgrade stale CI, coverage, graph, memory, and trajectory claims unless current changed paths and fresh command output confirm them.
