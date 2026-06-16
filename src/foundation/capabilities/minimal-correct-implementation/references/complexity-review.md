# Complexity Review

Load this reference for a complexity-only pass, AI-generated code bloat review, delete/shrink audit, or overengineering review. This pass complements normal correctness, security, reliability, architecture, and test review.

## Tags

- `delete`: remove dead, speculative, unused, duplicate, or stale flexibility.
- `stdlib`: replace hand-rolled code or dependency with standard library behavior.
- `native`: replace custom or dependency code with platform, framework, database, browser, or runtime behavior.
- `existing-code`: reuse an existing repository function, class, module, service, component, or test helper.
- `yagni`: remove one-implementation abstraction, unused config, scaffold-for-later, or dead flexibility.
- `shrink`: preserve behavior with fewer branches, smaller public surface, or simpler control flow.

## Finding Shape

```text
tag:
file:
finding:
evidence:
required action:
validation required:
normal review still required:
```

## Automatic Return Signals

- Dependency added for behavior already solved by stdlib/native/existing code.
- Interface, abstract class, factory, strategy, provider, or registry has one implementation and no current external contract.
- Wrapper only delegates and does not protect auth, retry, timeout, observability, translation, lifecycle, side-effect visibility, or public contract.
- Shared/common/utils/helper contains business vocabulary or module-specific assumptions.
- Feature flag, mode, kind, or config option lacks owner, default, lifecycle, current consumer, tests, or cleanup path.
- A file split has no object/module/owner/boundary evidence.
- Stale fallback, compatibility branch, scaffold-for-later, or dead feature path remains active.

## Review Boundary

Do not use this pass to approve correctness. After complexity findings are fixed, normal review still checks behavior, compatibility, security, reliability, accessibility, data integrity, and validation evidence.
