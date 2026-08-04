# Security Output And Gates

Load only when assigned L3-L5 analysis, implementation, or independent review needs mode-specific closure plus targeted proof for a selected security or privacy risk.

## Do Not Load

Do not load when the root contract or compact checklist is sufficient.
Do not load when no trust, data, dependency, cloud, secret, AI, or tool-authority boundary changes.
Named Layer 3 Skills own specialized mechanisms.

## Output Contract

Return exactly one mode closure, followed only by fields triggered by the selected risk:

1. **Analysis closure:**
   - Return the trust-boundary model, reachable abuse paths, selected controls, validation strategy, unknowns, residual exposure, and recommended next owner or step.
   - Make no claim of edits or approval.
2. **Task closure:** Return the actual control diff, denied abuse-case results run after the last material edit, preserved behavior, unverified exposure, and residual risk. Hand fresh evidence to the independent-review owner without self-approval.
3. **Review closure:**
   - Return `Approved`, `Returned`, or `Blocked` with severity-ranked findings, reviewed and unreviewed scope, and proof limits.
   - Use `Blocked` for inaccessible required evidence, naming missing evidence, unblock condition, repair owner, and handoff.
   - Make no repair to the target.
4. **Authorization and abuse path:** When the affected scope involves an actor, object, tenant, session, input, or output, state the authoritative identity. Name the reachable source-to-sink path, denied behavior, and affected invariant. Include evidence for the selected authorization, validation, or neutralization outcome.
5. **Secrets, supply chain, and cloud:** Return only fields for selected risks.
   - For secret risk, state deployment environment, lifecycle, and access boundary.
   - For dependency risk, state identity, provenance, and advisory evidence.
   - For cloud risk, state effective IAM, public or network exposure, and key exposure.
   - For every selected risk, state the owner and containment or rollback outcome.
6. **Privacy and compliance:** When classified data or regulated processing is affected, state data class, jurisdiction, purpose, recipients, and retention/deletion need. Also state the applicable policy or control objective, evidence owner, and any justified exception without assuming a universal legal basis.
7. **AI, tool, and evidence limits:** State untrusted inputs/outputs for any authority-boundary crossing. Covered surfaces are prompts, retrieval, model output, agents, connectors, scanners, shell, IaC, and network writes. Also state allowed actions/data, permission or isolation evidence, abuse tests, proof limits, and residual exfiltration or unsafe-action risk.

## Quality Gate

1. When an actor can control resource identity, tenant, parent scope, filter, or indirect reference, require server-side authorization and denied cross-scope proof. Ownership predicates, tenant-scoped queries, or policy checks are candidates selected from the current authorization model.
2. When ambient browser credentials can authorize an unsafe state change, require request-integrity evidence through a control selected from the actual browser and authentication flow.
3. When attacker-controlled data reaches SQL, shell, template, HTML, URL-fetch, file, prompt, retrieval, or tool sinks, require context-specific neutralization and malicious-path proof. Parameterization, contextual encoding, parsers, allowlists, isolation, or sandboxing are candidates selected from sink semantics.
4. When secret material is required, prove bounded exposure, access ownership, rotation/revocation, and audit behavior appropriate to deployment and policy. Workload identity, managed secret services, orchestrator secrets, or encrypted configuration are candidates; no mechanism is universal.
5. When a vulnerability or dependency finding is Critical or High, choose repair, remediation, exception, or block.
   - Base the choice on validated severity, reachability, ownership, controls, and release policy.
   - Retain scanner uncertainty in the decision.
6. When privacy or compliance risk is triggered, require actual classification, jurisdiction, purpose, retention or deletion need, and applicable policy evidence. Triggered cloud governance instead carries effective IAM, network exposure, key policy, environment, owner, and rollback evidence. Candidate controls remain limited to applicable obligations.
7. When untrusted AI, retrieval output, or a tool can influence privileged actions or sensitive data, require authority boundaries.
   - Require denied-abuse proof through controls selected from reachable impact.
8. Bind a gate verdict to the assets, paths, environments, and controls actually inspected.
   - Use automated scans, policy diffs, negative tests, and manual review only for their named coverage.
   - Record untested environments, unknown consumers, third-party controls, and unenumerated abuse paths as residual exposure.
   - Assign the next owner.
