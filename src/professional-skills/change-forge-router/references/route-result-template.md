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

## 4. Runtime Prompt Execution Gates

### Requirement Clarification Gate
- Current behavior:
- Desired behavior:
- Non-goals:
- Constraints:
- Acceptance / TDD signal:
- Blocking questions:
- Assumptions:
- Clarification status: blocked / clarified / clarified-with-assumptions

### Read-Before-Plan Gate
- Files/code/config/tests/docs inspected before plan:
- Existing conventions found:
- Call-chain or ownership boundaries inspected:
- Not inspected:
- Risk accepted from not-inspected boundaries:

### TDD Plan Gate
- Failing or new test expected:
- Updated test/eval expected:
- Test/eval/validation command:
- Acceptance evidence:
- Not-verified fallback:

## 5. Impact Areas
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

## 6. Professional Skill Path
| Order | Skill | Why | Input | Output |
| --- | --- | --- | --- | --- |

## 7. Foundation Capabilities
| Capability ID | Capability | Why | Used By | Expected Output |
| --- | --- | --- | --- | --- |

## 8. Domain Extensions
| Extension | Why | Risks | Required Outputs |
| --- | --- | --- | --- |

## 9. Required References And Task DAG

### Required References
| Skill | Reference | Why | Required/Optional |
| --- | --- | --- | --- |

### Context Control
- Budget mode:
- Budget rationale:
- Selected capability/reference count:
- Selected references with rationale:
- Skipped references with rationale:
- JIT retrieval plan:
- Tool-output boundary:
- Compaction snapshot required:
- Branch route-repair summary required:
- Overhead evidence:
- Residual context risk:

### Task DAG
Each task:
- id
- name
- owner_skill
- capabilities
- depends_on
- files_or_artifacts
- acceptance
- tdd_or_validation_signal
- review_skill
- review_evidence
- repair_if_review_fails
- rollback_note

### Action Skill Map
| Action | Owner skill | Capabilities | Input | Output | Review skill | Review evidence | Repair route if review fails |
| --- | --- | --- | --- | --- | --- | --- | --- |

### Review And Repair Loop
- Review owner:
- Review result:
- Findings:
- Repair owner:
- Repair result:
- Re-review owner:
- Re-review result:
- Remaining risk:

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
- Primary product surface:
- Product surfaces:
- Primary language surface:
- Language surfaces:
- Stage-specific capabilities:
- Capabilities explicitly skipped:
- Skills explicitly skipped:
- Routes explicitly skipped:
- Skip rationale:
- Context budget decision:
- Required evidence:
- Required quality gates:
- Stage transition condition:
- Stage selection evidence:
- Stage conflicts ruled out:
- Next stage handoff:
