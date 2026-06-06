# Route Result Template

Deep reference for the ChangeForge Router Markdown Routing Result. The router body
summarizes this contract; this file is the single source of truth for the exact
human-readable result sections. Validators parse this file for quality gate and stage
fields so the router body can stay compact.

# ChangeForge Routing Result

## 1. Request Classification
- Change type:
- Complexity:
- Risk level:
- Execution mode:
- Product area:
- Code area:
- Domain extension signals:

## 2. Interpreted Change
- Current behavior:
- Desired behavior:
- User value:
- Constraints:
- Non-goals:

## 3. Missing Information
- Blocking:
- Non-blocking:
- Assumptions:

## 4. Impact Areas
- Product behavior:
- UX:
- Domain:
- API:
- Data:
- Frontend:
- Backend:
- Integration:
- Security:
- Testing:
- Reliability:
- Delivery:
- Documentation:

## 5. Professional Skill Path
| Order | Skill | Why | Input | Output |
| --- | --- | --- | --- | --- |

## 6. Foundation Capabilities
| Capability ID | Capability | Why | Used By | Expected Output |
| --- | --- | --- | --- | --- |

## 7. Domain Extensions
| Extension | Why | Risks | Required Outputs |
| --- | --- | --- | --- |

## 8. Required References
| Skill | Reference | Why | Required/Optional |
| --- | --- | --- | --- |

## 9. Task DAG
Each task:
- id
- name
- skill
- capabilities
- depends_on
- files_or_artifacts
- acceptance
- rollback_note

## 10. Quality Gates
- requirement gate
- impact gate
- domain gate
- architecture gate
- API/data gate
- implementation gate
- security gate
- test gate
- reliability gate
- delivery gate
- documentation gate
- AI review gate
- execution discipline gate

## 11. Next Actions
- next skill calls
- blocked/unblocked status
- recommended execution mode

## 12. Stage Professionalism
- Current engineering stage:
- Next engineering stage:
- Product surface:
- Language surface:
- Stage-specific capabilities:
- Capabilities explicitly skipped:
- Skip rationale:
- Context budget decision:
- Required evidence:
- Next stage handoff:
