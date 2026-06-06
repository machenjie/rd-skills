# Advanced Refactoring And Extension Reuse — Full Protocol

Deep reference for the `## Advanced Refactoring & Extension Reuse` rules in
`implementation-structure-design`. The capability body carries the decision-critical
summary; this file carries the full extension-safety conditions, the advanced refactoring
escalation protocol, and the record templates. It is loaded in the `dev` profile and by
skill authors.

## Extension Reuse Without Behavioral Drift

When an existing function, method, class, service, repository, adapter, component, hook, or module already owns the concept but lacks a case, prefer extending it over creating a parallel implementation only if all conditions hold:

- The original responsibility remains single and naturally named.
- Existing callers keep the same behavior.
- The extension is backward compatible.
- New parameters are optional or represented by a clear parameter object.
- No unrelated mode flags are added.
- No vague `type`, `kind`, `mode`, `flag`, or `strategy` switch is added unless the existing abstraction is already designed for that variation.
- Existing tests still pass.
- New tests cover both old behavior and newly supported behavior.
- Error behavior and edge cases remain compatible.
- The extension does not force the owner to import a forbidden layer.
- The extension does not turn the owner into a generic manager, processor, util, or mixed-responsibility branch pile.

Reject extension reuse when:

- the old function/class would become ambiguous;
- the new case belongs to a different owner;
- compatibility cannot be proven;
- tests cannot cover old and new behavior clearly;
- the extension requires cross-layer imports;
- the name would need to become vague to fit both old and new responsibilities.

The plan must include an Extension Safety Record:

- existing owner;
- missing case being added;
- old behavior preserved or changed;
- compatibility risk;
- tests covering old behavior;
- tests covering new behavior;
- rejected parallel implementation and why;
- confirmation that responsibility remains single.

## Advanced Refactoring Structure Protocol

When refactoring, evaluate these options in order:

1. Inline cleanup:
   - rename;
   - simplify condition;
   - remove duplication inside the same function;
   - reduce nested control flow.

2. Function extraction:
   - extract when a block has a nameable responsibility;
   - keep private if used once or only locally;
   - move to module-internal only when reused by multiple files in the module;
   - do not create a shared utility for one caller.

3. Object extraction:
   Extract a class/object only when at least one is true:
   - it owns state across multiple operations;
   - it protects invariants;
   - it models lifecycle transitions;
   - it coordinates collaborators;
   - it represents a domain object;
   - it represents a value object;
   - it represents a service object;
   - it represents an adapter;
   - it represents a strategy;
   - it represents a protocol participant;
   - it gives a real boundary that a function cannot express clearly.

4. Interface or protocol extraction:
   Extract only when:
   - multiple implementations exist now;
   - a test seam is needed for an external dependency;
   - framework/plugin boundaries require it;
   - dependency inversion removes a real architectural violation;
   - the interface expresses stable behavior rather than one implementation.

5. Inheritance:
   Use only when:
   - subtypes are genuinely substitutable;
   - the base class has a stable contract;
   - initialization and lifecycle are safe;
   - contract tests cover every subtype;
   - callers do not need to branch on concrete subtype;
   - inheritance is not being used merely for helper reuse.

   Reject inheritance when composition, delegation, strategy, or extraction is simpler.

6. Reflection or metadata-driven dispatch:
   Use only when:
   - framework integration requires it;
   - plugin discovery requires it;
   - schema/annotation/metadata mapping avoids repetitive boilerplate safely;
   - compile-time alternatives would create worse duplication or coupling.

   Reflection must include:
   - type-safety boundary;
   - failure behavior;
   - discoverability notes;
   - test coverage;
   - security consideration if inputs influence reflection;
   - fallback when metadata is missing or malformed.

The plan must include an Advanced Refactoring Decision:

- why inline cleanup is insufficient;
- why function extraction is insufficient or sufficient;
- why object/class/interface is justified or rejected;
- state/invariant/lifecycle/collaborator decision;
- composition vs inheritance decision;
- substitutability evidence if inheritance is used;
- reflection safety decision if reflection is used;
- public behavior tests used to prove the refactor.
