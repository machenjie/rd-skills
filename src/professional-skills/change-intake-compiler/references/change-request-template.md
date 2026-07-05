# Change Request Structure Template

Deep reference for the `change-intake-compiler` skill. The body enumerates the same fields in
its `Output Contract`; this file is the fill-in authoring template with per-field notes. It
ships with the skill in every profile.

```
## Change Request

**ID**: [CR-NNNN or issue reference]
**Source**: [Stakeholder name / issue URL / meeting date]
**Submitted by**: [Name and role]

### Summary
[One sentence: who does what and why]

### Current Behavior
[Observable state today — what happens now, including error messages, outputs, user experience]

### Desired Behavior
[Observable state after the change — what must be true when done, without specifying how]

### Non-Goals
[What will NOT change and must not be affected — equally important as goals]

### Constraints
[Technical, regulatory, time, resource, or compatibility constraints the implementation must respect]

### Assumptions
[Believed-to-be-true statements that have not been confirmed — each must be validated before implementation]

### Open Questions
[Unknown information required before implementation can proceed — each with proposed owner and due date]

### User Value
[Who benefits: role/persona, how they benefit, measurable improvement if known]

### Affected Surfaces
[Product features, APIs, data models, integrations, systems named at the product level]

### Completion Signal
[Observable, verifiable evidence that the change is done — testable condition, not a task checkbox]

### Risk Flags
[Early signals of impact, compliance, security, or rollback risk that downstream analysis must investigate]
```
