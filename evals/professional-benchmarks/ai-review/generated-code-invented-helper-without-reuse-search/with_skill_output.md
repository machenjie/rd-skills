Selected stage: code-review.
Selected professional skill: ai-code-review-refactor.
Selected capabilities: implementation-structure-design, code-clarity-maintainability, agent-execution-discipline, code-review.

Hidden risks: invented shared helper without reuse search; wrong placement and business vocabulary in shared code; AI-generated comments claiming unsupported universality.

Severity-classified findings:
- High: generated helper duplicates date formatting behavior without existing date formatting reuse search.
- Medium: shared/common/utils audit and owner decision are missing; business vocabulary does not belong in shared utility.
- Medium: AI-generated comments claim unsupported universality and must not be accepted as proof of intent.

Evidence required: existing date formatting reuse search; shared/common/utils audit and owner decision; validation command output or not-verified disclosure.

Reuse and placement rationale: inspect existing date formatters first; if behavior is feature-specific, keep it under the owning feature module rather than shared/common.

Validation command: not verified; required command is `npm test -- date-format`.
What evidence proves: reuse search and tests would prove no duplicate helper and preserved formatting behavior.
What evidence does not prove: locale/timezone correctness outside covered fixtures.

Output obligations covered: severity-classified findings; reuse and placement rationale; validation evidence and residual risk.

Residual risk: no fresh validation output yet.
Next gate: implementation-structure-design before accepting any helper placement.
