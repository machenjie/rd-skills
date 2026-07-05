# Regression Testing Benchmarks And Patterns

Use this reference when `regression-testing` needs deeper level selection, fixture fidelity, red/green replay, mutation/characterization strategy, hard-to-reproduce controls, or anti-pattern review. Keep `SKILL.md` focused on routing, evidence, output, and gates.

## Benchmark Anchors

- **TDD red-green repair:** prove the guard fails on the unfixed behavior and passes after the fix.
- **Test pyramid level selection:** choose the narrowest level that would have caught the defect.
- **Characterization testing:** lock current observable behavior before risky refactoring or extraction in historical defect zones.
- **FIRST principles:** regression tests should be fast enough, isolated, repeatable, self-validating, and timely.
- **OWASP verification practice:** fixed vulnerabilities need abuse/denied-path non-regression evidence without live unsafe side effects.
- **Mutation testing:** a useful regression guard fails when the original defect mutation is reintroduced.
- **DORA change-failure reduction:** regressions should become merge-gate evidence, not post-release detection only.

## Regression Level Selection Matrix

| Defect shape | Preferred guard | Escalate when | Avoid |
| --- | --- | --- | --- |
| Pure rule, parser, mapper, calculator, validator, or policy branch | Unit regression with exact trigger input/state | Real framework mapping or serialization caused the bug | E2E guard for a local deterministic rule |
| Repository query, ORM mapping, migration, cache, or transaction defect | Integration or persistence slice | Provider-specific behavior, constraint, or rollback caused the bug | Mocking the storage behavior that failed |
| API/service behavior, auth, permission, tenant, or object ownership defect | API/integration regression plus denied/non-leak assertion | Security boundary or same-pattern risk is broad | Absence-only assertion without abuse path |
| UI event, browser rendering, focus, or route behavior defect | Component or E2E regression at the smallest browser/UI boundary | Real browser behavior caused the bug | Testing only a private helper |
| Queue, retry, webhook, scheduler, or async job defect | Integration/component test with duplicate/retry/failure path | Ordering, replay, DLQ, or idempotency caused the bug | Sleep-based flake in CI |
| Race, timing, hardware, or production-only data defect | Deterministic replay, fake clock/scheduler, chaos experiment, monitoring, or documented impossibility | Lower environment cannot reproduce the condition | Unstable CI test as closure |

## Red/Green Replay Pattern

Use this sequence when feasible:

1. Protect dirty worktree and name rollback path.
2. Add or isolate the regression test without the fix.
3. Run the narrowest command against the pre-fix state and capture failure output.
4. Verify failure reason matches the original defect, not setup or assertion error.
5. Restore the fixed state and run the same command.
6. Record command, working directory, exit code, report/artifact path, and final-edit freshness.

If pre-fix replay is unsafe or impossible, record the explicit reason, rejected replay options, residual risk owner, and compensating proof.

## Fixture Fidelity Pattern

- Use the exact triggering input when safe and available.
- Use a minimized equivalent only when each removed field is irrelevant to the failure mechanism.
- Preserve role, tenant, ownership, feature flag, dependency response, ordering, timing, and data-shape preconditions.
- Redact or synthesize sensitive production data; record field transformations and owner.
- Own fixture update and reset paths so the regression does not rot after schema or generated-input changes.

## Hard-To-Reproduce Decision Tree

```text
Can a deterministic unit or integration replay reproduce the defect?
  YES -> write that regression guard and record red/green evidence.
  NO -> can a fake, stub, contract fixture, scheduler, clock, or generated input isolate it?
    YES -> use the deterministic substitute and state its limits.
    NO -> can a chaos experiment, canary monitor, alert, or manual runbook detect recurrence?
      YES -> document impossibility, compensating control, owner, and expiry.
      NO -> block closure until the risk owner accepts residual exposure.
```

## Mutation And Characterization Use

- Use mutation testing for money, permissions, eligibility, safety limits, state transitions, serialization, and critical comparisons.
- Promote a survived mutant that matches the original bug into a fixed regression case.
- Use characterization tests before refactoring legacy code when the intended behavior is current behavior preservation.
- Do not characterize known-bad behavior as permanent; pair it with an explicit defect record or migration plan.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| Test passes before and after fix | It never reproduced the defect |
| Fixture removes the original trigger | It protects a different behavior |
| E2E-only guard for a local rule | Slow fragile test is likely skipped or quarantined |
| Security fix with only happy-path authorization test | Abuse path can return through adjacent code |
| Old green CI cited after source or fixture edits | Evidence is stale |
| Flaky timing test added to CI | Teams learn to rerun or disable it |
| Missing defect link | Future maintainers delete the test as unclear |
| Shared database or provider state in test | Regression guard becomes order-dependent and unsafe |
