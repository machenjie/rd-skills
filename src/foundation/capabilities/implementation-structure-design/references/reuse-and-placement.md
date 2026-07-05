# Reuse And Placement — Full Protocol

Deep reference for the `## Reuse & Placement` rules in `implementation-structure-design`.
The capability body carries the decision-critical summary; this file carries the full
discovery protocol, the reuse ladder record template, and the function-placement decision
tree. It is loaded in the `dev` profile and by skill authors.

## Repository Local Pattern Discovery Protocol

Before adding or renaming any variable, parameter, field, function, method, class, struct, interface, component, hook, service, repository, adapter, helper, utility, file, package, module, or directory, inspect local conventions in this order:

1. Same file:
   - existing helpers;
   - private functions;
   - methods;
   - naming shape;
   - comment style;
   - error handling style;
   - test shape.

2. Same directory:
   - file naming pattern;
   - suffix/prefix convention;
   - public/private split;
   - test file naming;
   - sibling class/function naming;
   - local helper placement.

3. Parent directory or parent module:
   - module ownership;
   - exported API;
   - internal/shared boundary;
   - parent naming pattern;
   - existing package/module style.

4. Sibling modules:
   - equivalent feature/component/service/repository patterns;
   - similar naming and placement decisions.

5. Shared/common/utils:
   - only after proving the behavior is pure technical utility and domain-free;
   - never use shared/common/utils to avoid choosing the owning module.

6. Tests:
   - naming convention;
   - placement convention;
   - test helper/fixture style;
   - test comment style.

7. Generated or registry files:
   - whether new names require index/export/registration updates;
   - generated source-of-truth and regeneration policy.

The Implementation Structure Plan must state:

- files inspected;
- directories inspected;
- existing functions/classes/modules/services/repositories/hooks/components considered;
- detected naming convention;
- detected file naming convention;
- detected test naming convention;
- detected placement convention;
- reuse candidates found;
- rejected locations and why;
- final selected name and location;
- whether comments are required for the new or changed structure.

## Reuse Ladder

When adding behavior, choose the first valid option:

1. Direct reuse:
   - call an existing function, method, class, component, hook, service, repository, adapter, or utility with matching semantics.

2. Same-file extension:
   - extend an existing private helper, local function, or method if responsibility remains single.

3. Same-module extension:
   - extend an existing module-internal function, class, service, repository, adapter, or helper without changing old behavior.

4. Existing public API extension:
   - add a backward-compatible option, overload, parameter object, strategy, or branch only when the public contract remains coherent.

5. Composition:
   - compose existing functions/classes/services into the required behavior.

6. Adapter/wrapper:
   - wrap an existing behavior only when the call boundary, dependency direction, or external API shape requires adaptation.

7. Extraction:
   - extract duplicated or mixed behavior into a clearer private or module-internal abstraction.

8. New code:
   - create a new function/class/file/directory only after all previous levels are rejected with evidence.

Reject new code when an earlier ladder level can satisfy the requirement with lower structural cost.

The plan must include a Reuse Ladder Record:

- direct reuse candidates;
- same-file extension candidates;
- same-module extension candidates;
- existing public API extension candidates;
- composition candidates;
- adapter/wrapper candidates;
- extraction candidates;
- final decision;
- why lower-cost reuse levels were insufficient.

## Function Decision Tree

```text
Need new behavior?
|-- Does an existing function already implement the same semantic behavior?
|   |-- Yes: Reuse it directly.
|   `-- No
|-- Is there an existing function with the same concept but missing a case?
|   |-- Yes: Extend it only if its responsibility remains single and tests cover old and new behavior.
|   `-- No
|-- Is this behavior private to one file or class?
|   |-- Yes: Add a private or local helper in the same file.
|   `-- No
|-- Is this behavior private to one module?
|   |-- Yes: Add a module-internal function.
|   `-- No
|-- Is this behavior a stable public contract used by multiple modules?
|   |-- Yes: Add to the module public API with compatibility review.
|   `-- No: Keep local; do not export.
```
