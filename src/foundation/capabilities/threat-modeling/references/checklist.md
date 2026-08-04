# Threat Modeling Checklist

- Bound the task-local security delta: protected asset or authority, changed entry point, trust transition, data or control flow, downstream effect, and unknown edges.
- State the protected outcome before assigning likelihood, impact, blast radius, or priority.
- Identify actors whose current capability and preconditions make a path reachable, including legitimate-user, insider, service, partner, and compromised-component behavior when applicable.
- Trace source, controlled or stale values, transformations, policy or parser decisions, storage or transport, sink, and effect for each material path.
- Separate current evidence, assumptions, unreachable branches, uninspected siblings, and externally owned graph edges.
- Compare candidate controls by intercepted edge, protected outcome, authority, owner, failure behavior, compatibility, and bypass surface.
- Map the selected control to current implementation or configuration evidence and an applicable abuse or negative test.
- Define a monitoring, audit, reconciliation, or review signal when a material path can remain or recur, including safe fields and owner.
- Record residual consequence, compensating or containment evidence, accountable decision, release effect, and assumption-change or incident reopen trigger.
- State what repository, test, scan, design, owner, external, deployed, and production evidence does not prove.
