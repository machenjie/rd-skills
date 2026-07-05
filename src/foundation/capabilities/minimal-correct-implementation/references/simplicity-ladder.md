# Simplicity Ladder

Load this reference when a change adds a dependency, abstraction, function, class, file, directory, helper, wrapper, configuration option, or new structure.

## Decision Order

1. Does the work need to exist now?
2. Can existing repository code solve it?
3. Can the standard library solve it?
4. Can a native platform, framework, database, browser, or runtime feature solve it?
5. Can an already-installed dependency solve it?
6. Can a local one-line or small local implementation solve it?
7. Only then add the smallest correct new code.

## Evidence Per Step

- **Existence:** current requirement, acceptance signal, non-goal or rejected speculative work.
- **Existing code:** search scope, candidate names, owner modules, rejected reuse reason.
- **Standard library:** API considered, correctness match, edge cases, test or doc evidence.
- **Native feature:** framework/platform/database/browser/runtime primitive considered, boundary where it applies, mismatch if rejected.
- **Installed dependency:** package already present, approved owner, version/API verified, no wider transitive surface.
- **Local minimal code:** why a tiny local implementation is clearer and safer than a shared abstraction.
- **New code/dependency/abstraction:** current force, placement, validation, rollback/delete path, and residual risk.

## Current Force Rules

- One current implementation is direct code by default.
- Two current implementations may justify a shared local function or policy only if the shared behavior has one owner.
- Multiple current variants with a stable contract may justify strategy, factory, interface, provider, or registry.
- A future variant without current force is not a requirement.
- A config option with no current setter, owner, default, lifecycle, and tests is not a requirement.

## File Boundary Rule

Do not use "fewest files possible" as a rule. A new file is valid when it protects an owner, object, module, side-effect, adapter, generated/handwritten, public contract, lifecycle, test, or current strategy boundary. A new file is suspect when it exists only to reduce line count, expose a private helper, or make one local behavior look modular.

## Minimal Validation

L1 low-risk work may use the smallest meaningful runnable check. The check must fail when the relevant logic breaks. Higher-risk behavior keeps the normal depth required by `quality-test-gate`.
