Selected stage: implementation-preparation.
Route: Analyzed Work.
Start Profile: analysis-agent.
Primary Professional Skill: engineering-change-analysis.
Layer 3 Skills: repository-context-map.
Review Skill: architecture-impact-reviewer.
Execution Level: L4.
Level Basis: the rule owner and module boundary are unresolved. Existing helpers and consumers were not inspected.

Required risks:
- existing order-status owner is unknown
- shared utility placement can invert dependency direction
- caller invariants may diverge across services

Required evidence:
- repository search for existing order-status implementations
- verified consumers and dependency edges
- owner and boundary evidence with proof limits

Required outputs:
- current-behavior and owner map
- placement decision inputs and unresolved boundary
- analysis-only evidence-gathering step

Evidence-gathering step: search repository definitions, imports, callers, tests, and current module ownership before proposing placement.
This step gathers analysis evidence only. It is not an authoritative or dispatchable implementation slice.
Stop before implementation. Do not create the helper, select its owner, choose placement, or claim validation until the evidence is current.
Proof limits: this is a captured fixture. It proves the required analysis contract, not repository inspection, owner resolution, placement, implementation, tests, or production behavior.
