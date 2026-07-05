# Prototype Description Evidence Patterns

Use this reference when closure depends on proving that UI intent, state obligations, accessibility behavior, component reuse, and handoff limits are buildable and not overclaimed. Keep `SKILL.md` for routing and output shape; load this file only for concrete evidence mapping.

## Claim To Evidence Map

| Claim | Strong evidence | Weak or invalid evidence | Residual risk if absent |
| --- | --- | --- | --- |
| Hierarchy follows user decision order | Product/user goal plus ordered content rationale | Database field order or visual mock only | Implementation optimizes for code shape, not user task |
| States are implementation-ready | Idle/loading/empty/field-error/system-error/disabled/success obligations | "Handle loading and errors" | Blank screens, duplicate submit, and untestable UI states |
| Accessibility behavior is defined | Keyboard order, focus target, role/label/live-region, color-independent feedback | Generic "accessible" statement | Keyboard and screen-reader users cannot complete task |
| Design-system reuse is proven | Existing components inspected, accepted/rejected reuse, owner for new variant | "Use whatever fits" | Duplicate inaccessible component patterns |
| Destructive or sensitive flow is safe | Confirmation, consequence copy, preservation/recovery, security/privacy handoff | Button label only | Accidental destructive action or sensitive data exposure |
| Prototype scope is bounded | Local entry/exit context plus handoff to flow/state/design/frontend owner | Multi-page behavior buried in one brief | Flow or routing defects hidden from the right owner |

## Changed Prototype To Validation Map

For each hierarchy decision, action, validation rule, state, accessibility obligation, reuse decision, sensitive/destructive behavior, and open decision, record:

```yaml
prototype_validation_map:
  decision: ""
  surface_or_flow_context: ""
  evidence_or_review: ""
  validation:
    command_or_artifact: ""
    exit_code: null
    proves: ""
    does_not_prove: ""
  handoff_owner: ""
  residual_risk:
    owner: ""
    reason: ""
```

## Closure Checks

- Reject closure when a brief says "accessible" without keyboard, focus, label/role, and color-independence behavior.
- Reject closure when a table/list/form/modal lacks explicit loading, empty, error, disabled, and success obligations or a state-model handoff.
- Downgrade design-system reuse claims when existing components were not inspected or candidate gaps were not recorded.
- Do not treat a prototype brief as visual design approval, accessibility certification, frontend implementation, or product research proof.
