# AI Review Pattern Catalog

Load this reference when concrete examples are needed to calibrate hallucinated APIs, silent failure, over-abstraction, helper bags, side-effect pollution, mock-only tests, feature-flag debt, dependency pollution, or other recurring AI-generated failure modes.

## Anti-Examples

| AI Output Pattern | Problem | Correction Direction To Report |
|---|---|---|
| `lodash.deepClone(obj)` using a non-existent method | Hallucinated API and unproven clone semantics | Report the invalid API, reachable value-shape impact, and the unresolved clone-equivalence boundary below. |
| `catch (e) {}` | Silent failure | Report the lost error signal and identify the required observable error policy. |
| New `AbstractFactory` for one implementation | Over-abstraction | Report the unsupported variation and identify the simplest ownership boundary justified by current behavior. |
| New stateless `Helper` class with unrelated methods | Helper bag | Report the ownership diffusion and identify the behavior's owning object, module, or local boundary. |
| Policy function writes to database and emits events | Side-effect pollution | Report the mixed responsibilities and identify the policy, orchestration, and adapter boundaries. |
| Business fixture added to shared test utils | Test ownership pollution | Report the ownership leak and identify the owning module's test boundary. |
| Feature flag added with no cleanup path | Permanent compatibility debt | Report the lifecycle gap and identify required ownership, expiry, old/new proof, and retirement evidence. |
| Test asserts `expect(mockFn).toHaveBeenCalled()` only | Mock-only test | Report the missing behavior proof and identify the observable output or side-effect oracle. |
| `import { compress } from 'lz4-wasm'` as a new dependency | Undeclared dependency | Report the dependency risk and identify API, CVE, license, runtime, and existing-alternative evidence gaps. |

## Clone Equivalence Evidence

Treat `structuredClone` and `_.cloneDeep` only as candidates after semantic-equivalence proof for the accepted task domain.

| Evidence dimension | Required proof |
|---|---|
| Accepted values | Representative task-specific values cover the accepted value categories. |
| Identity and descriptors | Prototype or class identity, accessors, non-enumerable properties, and symbols retain the required semantics. |
| Executable and graph values | Functions and circular references preserve required behavior or fail as the current contract requires. |
| Transfer semantics | Transferable values preserve required ownership, detachment, and error behavior. |
| Runtime boundary | The supported runtime and version expose the candidate with the required semantics. |
| Failure behavior | Unsupported values and clone failures produce contract-compatible errors and side effects. |

Report task-specific equivalence tests for the applicable dimensions. When proof is unavailable, report the evidence gap without selecting either candidate.

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
