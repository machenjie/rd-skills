# Review Feedback Triage

- Bind each comment to its source commit, current code, and relevant contract.
- Classify outdated, resolved, duplicate, conflicting, and still-applicable feedback.
- Distinguish a defect, suggestion, preference, question, and out-of-scope request.
- Verify the claimed failure before accepting a proposed repair.
- Resolve conflicting advice against behavior, constraints, and current evidence.
- Explain rejected feedback or an alternative with a concrete technical reason.
- Map accepted feedback to the owning code change, validation, and remaining risk.
- Keep technical triage, implementation, external replies, thread resolution, and requesting review as separate authorized actions.
- Leave independent review read-only; implement accepted repairs through the code owner.
- Reuse existing Git conflict and rebase methods when history changes invalidate comments.

| Comment state | Disposition |
|---|---|
| Line moved but the same failure remains | Rebind and repair the current mechanism |
| Earlier commit contains an already-fixed defect | Cite the current fix and relevant validation |
| Preference conflicts with a required contract | Preserve the contract and explain the tradeoff |
| Valid defect exceeds the current scope | Record impact and obtain the missing scope decision |
| Code is repaired locally | Do not infer authority to send or resolve an external thread |
