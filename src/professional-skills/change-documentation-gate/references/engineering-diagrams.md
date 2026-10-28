# Engineering Diagrams

Use for a documentation diagram of supplied facts or an accepted design. Match depth to the user's question and available evidence. Draw a supplied three-step flow directly; no outline, reader proxy, approval, or independent review is needed.

## Choose The View

State the question and scope through a title, caption, or labels. Use the relationship the reader needs:

| Relationship | Useful view | Meaning to preserve |
| --- | --- | --- |
| Control flow | Flowchart or activity view | Actions, decisions, branch conditions, and relevant exits. |
| Interaction | Sequence view | Participants, call/message direction, ordering, replies, and synchronous versus asynchronous delivery. |
| State | State-transition view | States of one entity, events/guards, transitions, terminal outcomes, and forbidden transitions relevant to the question. |
| Structure | Component, dependency, or deployment view | Containment versus dependency, edge direction/meaning, and logical components versus physical hosts or replicas. |

## Preserve Meaning

- Keep node identities, edge meanings, and abstraction level consistent. Separate views when mixing call order, state changes, and deployment placement would imply false relationships.
- Keep branches needed to answer the question, including failure, timeout, retry, cancellation, or compensation when material. Simplify incidental detail, but label omitted paths or a happy-path scope instead of calling a partial view complete.
- Use documented facts and accepted decisions without inventing nodes, business rules, ordering, or deployment topology to make a diagram look complete.
- Return consequential factual gaps and unresolved business or architecture decisions to their owner.
- A diagram documents the chosen scope; it does not authorize changing implementation to make the picture true.

## Deliver And Check

- Use a maintainable source and target supported by the task, such as repository-native diagram text, an existing editor document, or a requested image export.
- Keep editable source when future maintenance requires it. A simple supplied flow needs no new tool installation.
- Compare nodes, relationships, branch conditions, and relevant outcomes with the source facts. For asynchronous interactions, distinguish acceptance from completion and preserve relevant retry, late-message, or cancellation semantics.
- Check syntax and target compatibility where applicable. Preview or render when layout, export, or the target carrier needs it, using available tooling; state unavailable checks. A successful render proves presentation, not semantic correctness.
- Return the diagram or its source with scope, omissions, and validation information needed by its consumer; no separate report or fixed rendering sequence is required.
