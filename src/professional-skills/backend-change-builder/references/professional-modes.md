# Backend Professional Modes

Owner: `backend-change-builder`.

Responsibility: provide the expanded mode contract for backend implementation,
review, debugging, refactoring, testing, reliability, and release-sensitive
changes. Load this reference only when the selected backend mode is L3+, touches
auth/data/async/release behavior, or the compact Mode Matrix in `SKILL.md` is not
enough to decide evidence obligations.

## New Backend Capability

- **Trigger signals:** new endpoint, command handler, use-case service, worker,
  repository method, validation policy, authorization policy, adapter, or domain
  service.
- **Professional focus:** decide the trust boundary, authoritative identity
  source, object ownership check, transaction boundary, idempotency requirement,
  placement, public/private API, and test level before implementation shape.
- **Required evidence:** existing controller/service/repository/validator/job
  patterns inspected; reuse candidates named; request/command schema, auth path,
  transaction scope, idempotency scope, error taxonomy, and test obligations
  stated.
- **Common hidden risks:** client-supplied identity trusted; business logic placed
  in common helpers; new repository bypasses tenant filter; no duplicate-delivery
  behavior; new endpoint has no denied-case test.
- **Companion capabilities/gates:** `controller-api-implementation`,
  `service-business-logic`, `repository-persistence`,
  `authentication-authorization`, `implementation-structure-design`,
  `quality-test-gate`.
- **Explicit skip guidance:** do not launch release, deep reliability, or
  architecture gates unless the new capability changes deployment topology,
  async behavior, production SLO path, public contract, or ownership boundary.

## Modify Existing Backend Logic

- **Trigger signals:** existing service/repository/validator/job/policy is edited;
  a branch, query, error condition, retry, or policy changes; old tests require
  updates.
- **Professional focus:** isolate the changed invariant and preserve compatible
  behavior for callers, contracts, errors, auth, transactions, and side effects.
- **Required evidence:** callers inspected; current tests and fixtures read;
  old/new behavior stated; compatibility and error semantics checked; changed
  branches covered.
- **Common hidden risks:** one branch changes object ownership semantics; fixture
  update hides old behavior; silent error fallback changes client behavior; query
  filter loses tenant scope.
- **Companion capabilities/gates:** `code-clarity-maintainability`,
  `regression-testing`, `change-impact-analyzer`, `data-api-contract-changer`
  when public contracts move.
- **Explicit skip guidance:** do not add new shared abstractions or broad
  refactors unless behavior-preservation evidence exists.

## Bug Fix

- **Trigger signals:** failing test, bug report, incident symptom, wrong error
  response, data inconsistency, permission leak, or local backend patch.
- **Professional focus:** verify root cause before mutation, scan for the same
  defect pattern, add regression evidence, and define the local vs. broad fix
  boundary.
- **Required evidence:** reproduction or failing test; verified cause statement;
  same-pattern search terms and paths; related occurrences; regression test or
  explicit non-testable rationale; behavior preservation statement.
- **Common hidden risks:** fixing only one endpoint while sibling endpoints leak;
  patching symptom without cause; updating snapshots instead of behavior; retrying
  the same failing approach.
- **Companion capabilities/gates:** `failure-diagnosis`,
  `agent-execution-discipline`, `regression-testing`, `quality-test-gate`.
- **Explicit skip guidance:** do not perform opportunistic cleanup outside the
  defect boundary unless it is required to fix the verified cause safely.

## Debugging Diagnosis

- **Trigger signals:** unknown root cause, intermittent failure, timeout,
  duplicate side effect, missing job, inconsistent state, queue lag, unclear logs,
  or "probably" language.
- **Professional focus:** separate observations from hypotheses, collect enough
  evidence to verify cause, and avoid code mutation before diagnosis unless
  adding reversible instrumentation.
- **Required evidence:** reproduction steps; logs/traces/metrics inspected;
  data sample or queue state inspected; hypotheses ruled in/out; next diagnostic
  probe or safe patch justified.
- **Common hidden risks:** diagnosing from the last visible symptom; missing
  correlation IDs; ignoring async redelivery; hidden version skew during rolling
  deploy; same-path retry after failures.
- **Companion capabilities/gates:** `failure-diagnosis`, `observability`,
  `logging-error-handling`, `agent-execution-discipline`.
- **Explicit skip guidance:** do not change business logic until cause is verified
  or the change is limited to reversible diagnostic evidence.

## AI Generated Backend Code Review

- **Trigger signals:** generated service/helper/repository/DTO/job code, broad AI
  patch, invented imports, new abstraction, duplicated logic, or missing tests.
- **Professional focus:** classify severity, detect hallucinated APIs, inspect
  reuse and placement, find hidden behavior change, and require validation
  evidence.
- **Required evidence:** existing API/helper search; same-pattern scan; typecheck,
  test, or build output; old behavior and public contract comparison; severity
  findings with file/line references.
- **Common hidden risks:** helper invented instead of reusing local pattern; logic
  placed in common/utils; private behavior tested directly; hidden auth or error
  behavior change; no command output.
- **Companion capabilities/gates:** `ai-code-review-refactor`,
  `implementation-structure-design`, `code-clarity-maintainability`,
  `code-review`, `quality-test-gate`.
- **Explicit skip guidance:** do not rewrite before review findings are classified
  and the safe refactor boundary is named.

## Behavior-Preserving Refactor

- **Trigger signals:** move, extract, split, rename, delete dead code, retire flag,
  reduce duplication, or simplify control flow without intended behavior change.
- **Professional focus:** preserve public behavior, auth checks, transaction
  semantics, idempotency, error taxonomy, logs, and side effects while improving
  structure.
- **Required evidence:** affected callers; before/after test coverage; deletion
  path; compatibility branch owner/expiry; placement rationale; no-contract-change
  statement.
- **Common hidden risks:** moved code changes transaction timing; extracted helper
  widens visibility; deleted branch still used by old clients; refactor silently
  changes error code or audit behavior.
- **Companion capabilities/gates:** `refactoring`,
  `implementation-structure-design`, `code-clarity-maintainability`,
  `quality-test-gate`.
- **Explicit skip guidance:** do not add new behavior, new public DTOs, or release
  migrations in the same refactor patch.

## Performance Or Reliability Fix

- **Trigger signals:** N+1 query, latency regression, timeout, saturation, queue
  lag, retry storm, duplicate side effect, race condition, pool exhaustion, or
  incident mitigation.
- **Professional focus:** prove bottleneck or failure mode, bound load and retries,
  preserve idempotency, add observability, and prevent new contention or fallback
  risk.
- **Required evidence:** baseline metric or profile; resource dimension affected;
  retry/backoff and idempotency behavior; concurrency model; metric/alert/log
  evidence; test or load-check limitation.
- **Common hidden risks:** retry amplifies outage; cache fix hides stale data;
  connection pool default is too low; queue consumer ACK loses work; local
  benchmark ignores production data size.
- **Companion capabilities/gates:** `profiling`, `performance-budgeting`,
  `concurrency-control`, `degradation-circuit-breaking`, `observability`,
  `reliability-observability-gate`.
- **Explicit skip guidance:** do not accept readability regressions or broad
  speculative optimization without measured bottleneck evidence.

## Release Or Migration-Sensitive Backend Change

- **Trigger signals:** schema migration, config change, feature flag, rollout
  window, old/new version coexistence, irreversible mutation, public DTO/error
  change, or rollback question.
- **Professional focus:** guarantee compatibility during deployment, define
  rollback and data recovery, preserve consumers, and make operational evidence
  available before rollout.
- **Required evidence:** expand/migrate/contract or rollout plan; config defaults;
  version-skew behavior; rollback command or explicit irreversible acceptance;
  migration validation; owner and monitoring signal.
- **Common hidden risks:** old code cannot read new state; contract cleanup ships
  before consumers migrate; feature flag default unsafe; rollback lacks data
  reversal; audit path missing for irreversible operation.
- **Companion capabilities/gates:** `delivery-release-gate`,
  `data-migration-design`, `version-compatibility`,
  `reliability-observability-gate`, `change-documentation-gate` when docs or
  runbooks change.
- **Explicit skip guidance:** do not perform contract removal, data contraction,
  or cleanup until consumer migration and rollback evidence are present.
