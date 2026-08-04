# Domain Impact Modeler Reference Index

Load only a reference that changes the current ownership, invariant, or validation decision.

| Reference | Load when | Do not load when |
| --- | --- | --- |
| [checklist.md](checklist.md) | Aggregate, rule, event, permission, transition, audit, or consistency surfaces need a compact coverage check. | The current source and tests already establish every relevant surface. |
| [evidence-patterns.md](evidence-patterns.md) | A domain rule needs source-to-test, event-consumer, owner, freshness, or residual-risk evidence. | The root output contract is sufficient for the bounded decision. |
| [business-invariant-evidence.md](business-invariant-evidence.md) | Business vocabulary, state transitions, calculations, or forbidden outcomes need explicit invariant proof. | No domain invariant changes. |
| [example-output.md](../examples/example-output.md) | A concise handoff example helps shape the output. | Example wording could be mistaken for current repository evidence. |
