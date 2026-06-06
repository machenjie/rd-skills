# Object Modeling — Full Decision Trees

Deep reference for the `## Object Modeling` rules in `implementation-structure-design`.
The capability body carries the decision-critical summary; this file carries the full
object, method, and class decision trees and the object-design rationale. It is loaded in
the `dev` profile and by skill authors.

## Object-Oriented Structure Decision Tree

```text
Considering object-oriented structure?
|-- Is there a real domain object, value object, service object, adapter, strategy, or protocol participant?
|   |-- Yes: Name the role, owner, lifecycle, collaborators, and observable behavior.
|   `-- No: Prefer a function, module operation, or plain data record.
|-- Does the object protect invariants or prevent invalid state transitions?
|   |-- Yes: Encapsulate state mutation and expose behavior-oriented methods.
|   `-- No
|-- Does the object only group stateless helpers or mirror DTO fields with getters/setters?
|   |-- Yes: Reject object; use functions, records, or module-local helpers.
|   `-- No
|-- Are multiple behavior variants required today?
|   |-- Yes: Prefer interface + composition, strategy, or delegation unless taxonomy is real.
|   `-- No: Do not pre-build extension points.
|-- Is inheritance being considered?
|   |-- Yes: Prove substitutability, base-class contract compatibility, initialization safety, and tests for each subtype.
|   `-- No: Keep composition/delegation explicit.
|-- Would callers need to know concrete subclasses or internal state to use it correctly?
|   |-- Yes: Boundary is leaky; redesign interface or keep logic local.
|   `-- No: Object boundary may be accepted with tests through public behavior.
```

Object design is a structural decision, not a name-only exercise. A good object name exposes stable responsibility and the boundary it protects. A bad object name such as generic manager, processor, helper, or util usually signals scattered procedural logic, a hidden data bag, or a hierarchy that future callers must understand to avoid invalid use.

Inheritance must be treated as a public contract. Every subtype must preserve base-class preconditions, postconditions, error behavior, and lifecycle expectations. If inheritance is only used to share helper code, replace it with composition, delegation, extraction, or a private helper.

## Method Placement Decision Tree

```text
Considering a method on an existing or new class?
|-- Does the method use or protect object state, invariants, lifecycle, or collaborators?
|   |-- Yes: Method placement may be appropriate.
|   `-- No
|-- Is the method behavior naturally expressed in the object's vocabulary?
|   |-- Yes: Keep near the object if dependency direction allows it.
|   `-- No: Use a service, module function, adapter, or local helper.
|-- Would adding the method force the object to import infrastructure or UI concerns?
|   |-- Yes: Reject; place orchestration in a service or adapter.
|   `-- No
|-- Does it make the class a generic manager/processor/helper?
|   |-- Yes: Split by responsibility or move behavior to the correct owner.
|   `-- No: Accept with tests through public behavior.
```

## Class Decision Tree

```text
Considering a new class?
|-- Does it own mutable state or lifecycle?
|   |-- Yes: Class may be appropriate.
|   `-- No
|-- Does it enforce invariants across multiple operations?
|   |-- Yes: Class, value object, or domain object may be appropriate.
|   `-- No
|-- Does it implement an interface or protocol with multiple concrete implementations today?
|   |-- Yes: Class or strategy may be appropriate.
|   `-- No
|-- Does it only group stateless helper functions?
|   |-- Yes: Reject class; use functions or module-local helpers.
|   `-- Continue
|-- Is it replacing a clear existing service or class?
|   |-- Yes: Extend or compose the existing class.
|   `-- Create only with owner, responsibility, tests, and dependency justification.
```
