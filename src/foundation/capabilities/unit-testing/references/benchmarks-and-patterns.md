# Unit Testing Benchmarks And Patterns

Use this reference when the inline capability is not enough to design high-signal unit evidence. Keep the unit claim narrow: it proves local behavior under controlled inputs, not real infrastructure, cross-service compatibility, browser behavior, production scale, or external provider behavior.

## Benchmark Anchors

- **TDD red-green-refactor:** write the smallest failing behavior test, make it pass, then refactor with the test still green.
- **FIRST principles:** unit tests should be fast, isolated or independent, repeatable, self-validating, and timely.
- **xUnit Test Patterns:** choose stubs, mocks, fakes, and spies by behavior boundary and fidelity need.
- **Boundary Value Analysis:** test exact edges, just-below, just-above, empty, max, overflow, and invalid values.
- **Equivalence Partitioning:** group inputs that should follow the same rule, then test representatives plus boundaries.
- **Mutation testing:** survived mutants show assertions that execute code without proving rule correctness.
- **Property-based testing:** generated inputs are useful when invariants matter more than individual examples.
- **Behavior-focused testing:** assert outcomes visible through public/module boundaries, not private method choreography.

## Unit Case Matrix Pattern

Start from the rule, not the implementation branch names.

| Case class | Question | Example evidence |
| --- | --- | --- |
| Representative success | What ordinary input proves the intended rule? | Active annual account receives the expected renewal discount. |
| Lower boundary | What is the smallest valid value? | Cart total `0.00` produces no discount. |
| Upper boundary | What is the highest valid value or final tier? | Cart total `200.00` enters the 15 percent tier. |
| Just below boundary | What value should remain in the previous class? | Cart total `99.99` stays below the 10 percent tier. |
| Just above boundary | What value should enter the next class? | Cart total `100.01` receives the higher tier when currency rules allow it. |
| Invalid value | What input must be rejected? | Negative total raises a domain validation error. |
| Missing value | What happens for null, absent, empty, or malformed input? | Missing account ID is rejected before calculation. |
| Failure path | What domain or local dependency failure is expected? | Suspended account raises the documented policy error. |
| Invariant | What must never be violated? | Discount never exceeds cart total. |
| Regression trigger | What exact prior failure must stay blocked? | USD `10.005` rounds half-up to `10.01`. |

## Discount Matrix Example

```
Rule:
  total < 50          => 0 percent discount
  50 <= total < 100  => 5 percent discount
  100 <= total < 200 => 10 percent discount
  total >= 200       => 15 percent discount

Cases:
  0.00     -> 0.00   empty cart boundary
  49.99    -> 0.00   just below 5 percent tier
  50.00    -> 2.50   exact 5 percent tier entry
  99.99    -> 5.00   just below 10 percent tier with declared rounding
  100.00   -> 10.00  exact 10 percent tier entry
  199.99   -> 20.00  just below 15 percent tier with declared rounding
  200.00   -> 30.00  exact 15 percent tier entry
  -10.00   -> domain validation error
  null     -> input validation error
```

## Test Double Decision Matrix

| Double | Use when | Reject when | Evidence to record |
| --- | --- | --- | --- |
| Real collaborator | It is pure, fast, deterministic, and part of the local rule. | It performs I/O or depends on external state. | Why it remains in the unit boundary. |
| Stub | The collaborator only returns a controlled value and interaction is not the behavior. | Branch correctness depends on request details. | Stubbed response and branch covered. |
| Mock | The observable behavior is an external interaction such as sending one command. | It verifies private choreography or internal call order. | Interaction is the public/seam behavior and assertion limit. |
| Spy | The public outcome cannot expose an external call but the call is material. | It observes private helper calls. | Why direct state/output proof is unavailable. |
| Fake | Stateful behavior is needed but real infrastructure is too slow or unavailable. | Real constraints, transactions, serialization, or provider quirks carry the risk. | Fidelity source and required integration/contract follow-up. |

## Determinism Controls

- Freeze clock and timezone when dates, durations, TTLs, or schedules affect output.
- Seed or inject randomness and UUID generation; never assert against uncontrolled generated values.
- Reset globals, singletons, caches, registries, feature flags, environment variables, and module state in setup/teardown.
- Replace sleeps with controlled schedulers, fake timers, or explicit promise/task advancement.
- Own fixtures per module or domain boundary; broad shared object mothers need an owner and deletion path.
- Avoid execution-order dependence; each test creates all state it needs.

## Assertion Quality

Strong assertions name the behavior and check a result the caller can observe:

```typescript
await expect(service.placeOrder({ accountId: "a1", total: 50 }))
  .rejects.toThrow(InsufficientFundsError);
```

Weak assertions freeze implementation without proving correctness:

```typescript
expect(spyOnPrivateDiscountCalculator).toHaveBeenCalled();
```

Use one assertion group per behavior. Multiple assertions are acceptable when they describe the same outcome, such as return value plus emitted domain event. Split tests when one setup is trying to prove unrelated rules.

## Mutation And Property Triggers

Use mutation testing when logic includes money, permissions, eligibility, safety limits, stock, quota, state transitions, rounding, or critical comparisons. Survived mutants usually mean the test executed the branch but failed to assert the rule.

Use property-based testing when a rule is invariant-heavy:

- parsing then rendering returns an equivalent value;
- normalization is idempotent;
- sorting preserves item count and membership;
- discounts never exceed totals;
- serialization round-trips within declared precision;
- state transitions never skip terminal guards.

Record the generator domain, excluded invalid values, shrink behavior when known, seed/replay command, and any examples promoted to fixed regression cases.

## Graph, Memory, And Execution Coupling

Before accepting a unit-test claim, reconcile:

1. **Repository graph:** the owning module, public boundary, direct collaborators, fixture owners, generated inputs, and existing tests.
2. **Project memory:** prior fragile-file notes, incidents, failing cases, review comments, and stale summaries as leads only.
3. **Execution trajectory:** edits made after the last test run, changed mocks/fakes/fixtures, generated artifacts, and command order.
4. **Validation freshness:** final material source and test changes must precede the final evidence command.

If graph or memory claims cannot be source-confirmed, mark them `not_verified` or `stale`; do not use them as proof.

## Validation Map

| Change type | Minimum unit evidence | When to add another gate |
| --- | --- | --- |
| Pure rule or calculation | Unit case matrix plus deterministic command. | Integration only if the rule depends on real persistence or framework mapping. |
| Parser/normalizer | Representative, malformed, boundary, idempotence/property cases. | Contract test if serialized shape is consumer-visible. |
| Validator | Valid, invalid, missing, malformed, boundary, and error-message-safe cases. | Security gate if validation protects trust boundary. |
| Bug fix | Red/green regression unit with exact trigger. | Regression gate if red-before-fix is unavailable or disputed. |
| Refactor | Characterization tests before movement and final command after movement. | Testability seam gate if private helper export pressure appears. |
| Mock/fake update | Behavior assertion plus double limitation statement. | Integration/contract gate if double represents external provider behavior. |

## Anti-Patterns To Reject

- A test named after a private helper or implementation branch instead of behavior.
- A happy-path-only suite for a multi-branch rule.
- Mocking the pure helper that contains the rule under test.
- Asserting only snapshot text where semantic fields should be asserted.
- Using current time, random value, real sleep, global state, or unordered collection output without control.
- Treating line coverage, old green CI, or generated reports as proof without current changed-path mapping.
- Reporting unit tests as proof of SQL constraints, auth filters, queues, network behavior, browser rendering, or consumer compatibility.
