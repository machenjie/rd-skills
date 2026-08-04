Selected stage: implementation-preparation.
Route: Analyzed Work.
Start Profile: analysis-agent.
Primary Professional Skill: engineering-change-analysis.
Layer 3 Skills: repository-context-map.
Review Skill: architecture-impact-reviewer.
Execution Level: L4.
Level Basis: the rule owners, current consumers, and module boundary are unresolved. No actual diff exists.

Required risks:
- tenant permission authority may be hidden in a generic helper
- invoice-status behavior may change across callers
- subscription entitlement ownership may cross module boundaries

Required evidence:
- repository search for duplicate invoice calculations
- verified tenant invoice and subscription rule owners
- current consumers dependency edges and behavior tests

Required outputs:
- current-behavior and ownership map
- boundary evidence and unresolved shared-utils placement handoff
- analysis-only evidence-gathering step for owner discovery

Evidence-gathering step for owner discovery: inspect duplicate calculations, callers, permission checks, status transitions, entitlement rules, imports, and tests before choosing an owner or placement.
This step gathers analysis evidence only. It is not an authoritative or dispatchable implementation slice.
Stop before implementation. Do not move code, select the final boundary, or claim behavior preservation until the evidence is current.
`ai-code-review-refactor` is deferred until an actual diff exists.
Proof limits: this is a captured fixture. It proves the required analysis contract, not repository inspection, owner resolution, placement, implementation, tests, an actual diff, or production behavior.
