# AI Review Pattern Catalog

Load this reference when concrete examples are needed to calibrate hallucinated APIs, silent failure, over-abstraction, helper bags, side-effect pollution, mock-only tests, feature-flag debt, dependency pollution, or other recurring AI-generated failure modes.

## Anti-Examples

| AI Output Pattern | Problem | Required Action |
|---|---|---|
| `lodash.deepClone(obj)` using a non-existent method | Hallucinated API | Verify method name and version; replace with `structuredClone` or `_.cloneDeep` |
| `catch (e) {}` | Silent failure | Require logging, error propagation, or explicit ignore with comment |
| New `AbstractFactory` for one implementation | Over-abstraction | Collapse to direct instantiation; reintroduce factory when a second implementation exists |
| New stateless `Helper` class with unrelated methods | Helper bag | Move methods to owning objects/modules or collapse to local functions |
| Policy function writes to database and emits events | Side-effect pollution | Split pure policy from orchestrating service and adapter side effects |
| Business fixture added to shared test utils | Test ownership pollution | Move fixture/factory to owning module test boundary |
| Feature flag added with no cleanup path | Permanent compatibility debt | Add owner, expiry, old/new tests, and removal plan |
| Test asserts `expect(mockFn).toHaveBeenCalled()` only | Mock-only test | Add assertion on actual output or side effect |
| `import { compress } from 'lz4-wasm'` as a new dependency | Undeclared dependency | Run CVE/license review and evaluate a standard-library alternative |

## Failure Modes

- **Hallucinated API silently returns `undefined`** in dynamic languages; the feature ships broken and is discovered in production, not code review.
- **Over-abstraction hides simple logic** through factory/interface layers wrapping a single branch.
- **Dependency additions bloat attack surface** when a new package introduces transitive CVE or license risk without audit.
- **Tests pass only on mocks** because assertions check mock call counts instead of production behavior.
- **Silent behavioral divergence** appears when refactors preserve happy-path output but change edge cases.
- **Type annotation drift** appears when AI annotates a value as non-null even though runtime can return `null`.
- **Assumed singleton state breaks parallelism** when generated code relies on process-scoped mutable state.
- **Security bypasses hide behind plausible checks** such as case-sensitive role comparisons or missing tenant hierarchy.
- **Generated migrations lack rollback** when destructive DDL is accepted without expand/contract planning.
- **Generated comments describe intent, not behavior** and can cause reviewers to skip edge-case inspection.
- **Generated helper bags become permanent APIs** after unrelated methods gain public exports.
- **Generated side-effect pollution hides business decisions** when policies write databases, emit events, or call APIs.
- **Generated code only adds paths** while deprecated branches, feature flags, TODOs, and compatibility code remain without owner or expiry.
