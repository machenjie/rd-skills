---
name: change-intake-compiler
description: Converts raw user, stakeholder, issue, PR, bug report, or planning input into a structured Change Request covering current behavior, desired behavior, non-goals, constraints, assumptions, missing information, user value, and completion signal.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Change Intake Compiler

## Mission
Transform ambiguous, incomplete, or solution-premixed change input — from any source (user request, bug report, stakeholder instruction, PR description, planning session) — into a precise, structured Change Request that can be analyzed, impact-assessed, designed, implemented, reviewed, and verified without requiring further clarification from the original requester.

## When To Use
- The incoming request is incomplete: missing current behavior, desired outcome, constraints, or completion signal.
- The request conflates desired behavior with a specific implementation choice — solution-first framing that forecloses better alternatives.
- The request arrives spread across multiple channels (Slack thread, GitHub issue, email, meeting notes) and must be synthesized.
- The requester has stated a symptom (something is broken) rather than a desired behavior.
- Multiple stakeholders have contributed conflicting requirements that must be reconciled or surfaced as open questions.
- The implementation team cannot define "done" from the raw input without making undocumented assumptions.

## Do Not Use When
- The incoming change request is already complete with explicit current behavior, desired behavior, constraints, non-goals, and a verifiable completion signal accepted by responsible stakeholders.
- The request is a well-scoped, independently reviewable task card in an actively refined backlog.
- The request is a pure exploratory spike — output is a discovery artifact, not a behavioral change.

## Non-Negotiable Rules
- Strictly separate facts (observed behavior), assumptions (believed to be true), decisions (already made by stakeholder authority), and open questions (require resolution before proceeding).
- Non-goals and constraints must be preserved — removing them creates uncontrolled scope expansion.
- Never invent requirements to make the request feel complete — unknown information must surface as explicit open questions.
- Keep the change request implementation-neutral unless the requester has explicitly committed to a specific implementation approach.
- The Change Request must be verifiable: each desired behavior must map to an observable completion signal.
- User value must be explicit — who benefits, how, and by how much (if measurable).
- Affected surfaces at the product level (user-facing features, APIs, integrations, data) must be named, even if not fully analyzed.
- The Change Request is a contract between the requester and the implementer — it must not change silently; amendments require explicit review.

## Industry Benchmarks
- **Product Requirements Document (PRD) Standard**: Context, Problem Statement, Goals, Non-Goals, User Stories, Requirements, Constraints, Success Metrics — the complete structure that engineering and product share.
- **IEEE 830 / ISO/IEC 29148 (Software Requirements Specification)**: Requirements are complete, consistent, verifiable, unambiguous, traceable — the quality model for structured requirements.
- **Agile Story Mapping (Jeff Patton)**: Separate backbone activities from user tasks — prevents scope conflation and makes non-goals explicit.
- **Job-to-Be-Done Framework**: "When [situation], I want to [motivation], so I can [expected outcome]" — separates trigger, intent, and outcome from implementation.
- **Five Whys (Root Cause)**: For bug reports and incident-driven requests, the five-why chain surfaces the root behavior change needed, not just the symptom fix.
- **SMART Completion Signals**: Specific, Measurable, Achievable, Relevant, Time-bound — applied to the verification evidence in the Change Request.
- **RFC 2119 (Requirement Levels)**: Must, Should, May — distinguish mandatory requirements from desired enhancements from optional capabilities.

### Change Request Structure Template

The full Change Request template, with per-field authoring notes, lives in `references/change-request-template.md`; the same fields are enumerated in the Output Contract below.

## Technical Selection Criteria
Evaluate every field of the Change Request against:
- **Current behavior completeness**: Can an engineer reproduce the current state from this description alone?
- **Desired behavior precision**: Is the desired state observer-independent — would two engineers describe the same test for it?
- **Non-goal integrity**: Are the non-goals clear enough to prevent scope drift during implementation?
- **Constraint enforceability**: Can a reviewer confirm during code review that each constraint was respected?
- **Assumption traceability**: Is each assumption linked to a validation path (stakeholder question, data lookup, prototype)?
- **Open question ownership**: Does each open question have a named owner and a decision deadline?
- **User value measurability**: Can the user value claim be validated with product analytics, user research, or user acceptance testing?
- **Completion signal testability**: Can an automated test or structured manual verification be written for this completion signal today?

## Mode Matrix
Select the intake mode before compiling the Change Request.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| Ambiguity triage | Missing current behavior, desired behavior, non-goals, constraints, or completion signal. | Classify gaps as blocking questions vs non-blocking assumptions before downstream work. | Raw request excerpts mapped to fact, assumption, decision, or question; owner for each blocking question. | `requirement-clarification`, `requirement-structuring` | Impact, architecture, or implementation planning until blocking contract gaps are named. |
| Bug or incident intake | Symptom-only report, "used to work", logs without desired behavior, or unclear regression window. | Separate observed current behavior from expected restored behavior and acceptance readiness. | Repro inputs, affected actor, observed output, desired output, regression signal, evidence source. | `failure-diagnosis`, `acceptance-standard-definition` | Root-cause diagnosis unless requested separately. |
| Stakeholder conflict | Conflicting requests, multiple channels, scope pressure, or solution-first framing. | Preserve non-goals, constraints, authority, and assumption risk rather than choosing silently. | Conflict table with source, owner, decision needed, blocking status, and deadline. | `non-goal-boundary-definition`, `user-role-identification` | Design compromise or priority decision without authority. |
| Acceptance readiness | Intake is mostly complete but done state, negative path, or evidence is weak. | Convert intent into criteria-ready behavior without implementation coupling. | Completion signal, acceptance inputs, explicit not-accepted cases, non-verifiable gaps. | `acceptance-standard-definition`, `acceptance-criteria-builder` | Full task DAG until criteria readiness is confirmed. |
| Scope boundary repair | Request expands from local change into adjacent behavior, docs, migration, security, or release concerns. | Keep desired behavior narrow while surfacing downstream routing risks. | Affected surface list, non-goals, assumptions, residual unknowns, next gate. | `change-impact-analyzer`, `change-forge-router` | Loading specialist gates not implied by the intake evidence. |

## Proactive Professional Triggers
These triggers are hidden-risk escalators, not ordinary checklist items.

- **Signal:** The request says "just add/fix X" but omits current behavior, desired behavior, or completion signal. **Hidden risk:** downstream implementation optimizes for the wrong contract. **Required professional action:** stop at intake and compile observable current/desired behavior plus acceptance readiness. **Route to:** `requirement-clarification`, `acceptance-standard-definition`. **Evidence required:** gap classification as blocking question or non-blocking assumption with owner.
- **Signal:** A stakeholder names a solution such as cache, microservice, AI, or migration before naming the problem. **Hidden risk:** implementation locks into unnecessary architecture or data risk. **Required professional action:** rewrite as outcome-first desired behavior and preserve the proposed solution as a constraint or option. **Route to:** `requirement-structuring`, `architecture-impact-reviewer`. **Evidence required:** problem statement, non-goals, constraints, and rejected/accepted solution authority.
- **Signal:** Two sources describe different behavior, priority, role, date, or rollout expectation. **Hidden risk:** silent assumption becomes a hidden requirement and invalidates acceptance criteria. **Required professional action:** mark the conflict blocking when the answer changes contract, data, security, or acceptance. **Route to:** `non-goal-boundary-definition`, `change-impact-analyzer`. **Evidence required:** source excerpts, conflict owner, decision deadline, and safe assumption if non-blocking.
- **Signal:** A bug report contains only a symptom, screenshot, or failing output. **Hidden risk:** root cause work begins before the desired restored behavior is defined. **Required professional action:** capture reproducible current behavior and expected behavior before diagnosis. **Route to:** `failure-diagnosis`, `regression-testing`. **Evidence required:** repro condition, observed output, expected output, regression boundary, and not-yet-diagnosed disclosure.
- **Signal:** The requested change touches permissions, money, migration, external consumers, or irreversible user action but authority is not explicit. **Hidden risk:** wrong owner approves a high-impact contract or compliance change. **Required professional action:** elevate to blocking question and route specialist impact before implementation. **Route to:** `security-privacy-gate`, `data-api-contract-changer`, `delivery-release-gate`. **Evidence required:** named authority, affected surface, decision needed, and residual assumption risk.

### Decision Tree: Is the Request Ready to Proceed?

```
Is current behavior described observably?
├── No → Add "Current Behavior" with observable description
Is desired behavior described without implementation details?
├── No → Rewrite desired behavior to specify outcomes, not methods
Are non-goals explicit?
├── No → Add non-goals section; interview stakeholder if needed
Are all open questions listed with owners?
├── No → Surface open questions; do not resolve silently
Is the completion signal verifiable?
├── No → Rewrite as an observable, testable condition
All fields present and non-empty → Route to change-impact-analyzer
```

## Risk Escalation Rules
- Escalate when the request involves payment flows, financial state, user account actions, or account deletion without explicit authority confirmation.
- Escalate when the request implies a data migration, schema change, or irreversible data operation — the data owner must confirm scope.
- Escalate when the request implies regulatory compliance requirements (GDPR data subject rights, PCI, HIPAA, SOC 2) that require legal or compliance review.
- Escalate when the stated completion signal cannot be verified without access to production data or real user sessions.
- Escalate when two stakeholders have provided conflicting requirements — do not silently choose one; surface the conflict with a proposed resolution for stakeholder alignment.
- Escalate when the request affects a published API contract that has external consumers — impact assessment must include consumer notification planning.
- Escalate when cross-team or cross-system ownership boundaries are involved and no owner has been designated.

## Critical Details
- The most dangerous intake failure is treating a stakeholder-stated solution as the actual requirement — the real requirement is the outcome the solution is trying to achieve. Always ask "What problem does this solve?" and capture the answer in Current Behavior / Desired Behavior.
- Constraints are not suggestions — a constraint violated during implementation causes rework, not just technical debt. Preserve all stated constraints, even if they seem inconvenient.
- "It used to work" is not a current behavior description — extract the specific observable behavior that regressed, including the exact inputs, outputs, and conditions.
- Non-goals prevent scope creep — a team working on login performance must know that login UX redesign is explicitly out of scope. Without non-goals, both may happen or neither happens cleanly.
- Open questions that are resolved silently by the implementer become hidden requirements — they create delivery risk when the implied answer turns out to be wrong.
- Multiple communication sources (Slack, issue tracker, meeting notes) frequently contain contradictory statements from the same requester — synthesize and highlight contradictions in open questions, do not silently pick one.
- The Change Request is the contract for acceptance criteria — if the acceptance criteria builder cannot derive criteria from it, the request is not ready.
- Classify every gap as blocking or non-blocking with a hard rule: a gap is **blocking** when a wrong answer would change the contract, architecture, data model, security posture, or acceptance signal — capture it as an Open Question with an owner and deadline and do not start implementation. A gap is **non-blocking** only when any reasonable answer leaves the contract and acceptance unchanged — capture it as an explicit Assumption with a validation path. When unsure, treat the gap as blocking.

### Intake Analysis Techniques

- **Unimplementable-requirement detection**: flag a request that cannot be satisfied as stated — physically or technically impossible, internally self-contradictory, in conflict with a stated constraint or system invariant, or dependent on data the system does not and cannot hold. Return it as a blocking Open Question with the specific impossibility named and the closest implementable alternative proposed, rather than silently implementing a different thing.
- **Implicit non-goal identification**: infer the boundaries the requester assumed but did not state, and confirm them as explicit Non-Goals. A login-performance request usually implies "no login-UX redesign"; a copy fix usually implies "no layout change." Surfacing an implicit non-goal is cheaper than reverting unwanted scope.
- **Acceptance-signal reverse-derivation**: when no completion signal is given, derive it backward from "what observable evidence would convince the requester this is done?" Turn that evidence into a testable condition — automated test, structured manual check, or metric threshold — and feed it to `acceptance-criteria-builder`.
- **Business-term glossary generation**: extract every domain term in the raw input (entity, status, role, event, money or threshold term) and define it against the existing domain vocabulary. Flag any term used with two meanings, or a new synonym for an established concept, as a blocking ambiguity so naming stays consistent with `implementation-structure-design`.

### Anti-Examples

| Raw Input | Problem | Compiled Form |
|---|---|---|
| "Make the dashboard faster" | No current state, no threshold, no scope | "Dashboard load time exceeds 4 s for users with > 1,000 records (current); desired: load time < 1 s at p95 for all record counts; constraint: no schema changes in v1" |
| "Add Redis to the login service" | Solution-first, no problem statement | "Login token validation takes 300 ms (current); desired: < 50 ms without increasing database load; Redis is one possible implementation approach" |
| "Fix the bug from last week" | No current behavior described | "When a user submits the form with a duplicate email, the page displays a generic 500 error (current); desired: display 'Email already registered' with a link to login" |
| "We should support dark mode" | No completion signal | "When a user selects 'Dark' in display settings, all app surfaces render with WCAG AA compliant dark palette and the preference persists on reload" |

## Failure Modes
- **Solution conflation narrows options**: A stakeholder says "use a microservice" — the intake takes it as a requirement. The team builds an unnecessarily distributed system when a single-service change would have served the need.
- **Lost constraints cause rework**: A constraint ("must not require re-authentication") is omitted from intake. The implementation requires re-authentication. The feature is sent back after 3 weeks of development.
- **Silent assumption resolution hides delivery risk**: An implementer assumes the feature needs to work on mobile. It was scoped for desktop only. Mobile behavior is implemented incorrectly.
- **Missing completion signal enables subjective acceptance**: "The feature is done when it works" — no test can validate this, and stakeholders have different definitions of "works."
- **Conflicting requirements not surfaced**: Two stakeholders gave opposite requirements in two threads. The implementer chose one and the other stakeholder rejects the result at demo time.
- **Open questions treated as unknowns by accident**: A field is marked "unknown" instead of as a structured open question — no owner, no deadline, no follow-up, and the decision blocks implementation indefinitely.
- **Non-goals added post-implementation**: A team adds a feature the requester didn't want and didn't say they didn't want. Non-goals prevent this.
- **Current behavior described as desired**: "Users cannot currently log in with Google" is stated as current behavior — but it was never in scope. The Change Request conflates current state with desired state.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return a structured Change Request containing:
- **Mode selected**: Intake mode and signal that selected it.
- **Summary**: Single-sentence behavioral statement (actor, action, motivation).
- **Current Behavior**: Observable state today — reproducible by a reader with system access.
- **Desired Behavior**: Observable state after the change — implementation-neutral, verifiable.
- **Non-Goals**: Explicit list of what must not change and is out of scope.
- **Constraints**: Technical, regulatory, resource, or compatibility constraints.
- **Assumptions**: Believed-to-be-true statements with validation path.
- **Open Questions**: Unknown information with proposed owner and due date.
- **User Value**: Who benefits and how — measurable where possible.
- **Affected Surfaces**: Product-level surface names (no implementation detail required yet).
- **Completion Signal**: Verifiable observable condition, not a task checkbox.
- **Risk Flags**: Early signals for downstream specialist routing.
- **Boundaries inspected**: Source channels, stakeholder authority, product surfaces, non-goals, constraints, and explicit boundaries not inspected.
- **Professional judgment**: Which gaps are blocking, which assumptions are safe, and why acceptance is or is not ready.
- **Reuse and placement rationale**: Existing issue, PRD, template, glossary, or domain vocabulary reused; new intake artifact location and owner when one is created.
- **Behavior preservation statement**: Existing behavior and non-goals that must not change while implementing the desired behavior.
- **Validation evidence**: Source excerpts, reproduced behavior, stakeholder confirmation, or not-verified disclosure.
- **Evidence limits**: What the intake evidence proves and what it does not prove about impact, implementation, rollout, or root cause.
- **Residual risk**: Remaining assumption risk, owner, deadline, and blocked/unblocked status.
- **Next gate / handoff**: Next professional skill or explicit no-next-gate rationale.

## Evidence Contract
Close an intake compile only when all canonical evidence answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: raw input source, selected mode, and the requirement-quality rule used to classify readiness.
- **Files and boundaries inspected**: issue, PR, transcript, screenshot, logs, source docs, affected product surfaces, stakeholder authority, constraints, and non-goals inspected or explicitly unavailable.
- **Placement rationale**: where the structured Change Request belongs, which existing artifact or vocabulary was reused, and why no implementation location is being decided yet.
- **Validation commands**: source lookup, repro command, stakeholder confirmation, or structured manual check used to validate current behavior and completion signal.
- **Intake judgment and evidence limits**: blocking vs non-blocking questions, assumptions accepted, what evidence proves, what it does not prove, residual risk, and next gate.

## Quality Gate
1. Current behavior is described observably — a reader with system access can reproduce it.
2. Desired behavior is implementation-neutral and observer-independent.
3. Non-goals exist and are specific enough to prevent scope drift.
4. All constraints are explicit and enforceable during review.
5. Assumptions are distinguished from facts and have validation paths.
6. Open questions are listed with named owners and decision deadlines — none resolved silently.
7. User value is stated and traces to a beneficiary and a measurable outcome or proxy.
8. Completion signal is testable by automated test or structured manual verification.
9. Affected surfaces are named at the product level.
10. The Change Request can stand alone — an implementer who was not in any discussion can build the correct thing from this document.

## Handoff
- **change-impact-analyzer** — when the compiled Change Request reveals multi-surface impact requiring blast radius analysis.
- **acceptance-criteria-builder** — when the Change Request is ready to be converted into verifiable acceptance criteria.
- **domain-impact-modeler** — when domain business rules, invariants, or state transitions are implied by the desired behavior.
- **task-dag-planner** — when a multi-phase implementation requires sequencing and dependency management.
- **change-forge-router** — when the scope of the change requires routing to multiple specialist skills.

## Completion Criteria
The raw change input has been transformed into a structured, stakeholder-reviewed Change Request where current and desired behaviors are observable, non-goals prevent scope drift, constraints are explicit, all open questions have owners, assumptions are validated or scheduled for validation, the completion signal is testable, and the request stands alone without requiring verbal clarification from the original requester.
