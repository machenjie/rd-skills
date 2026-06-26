# Layered Architecture Design Checklist

- Select the layering mode and scope the use case, module/package boundary, included layers, and excluded surfaces.
- Record current source evidence: entry points, services/use cases, domain objects, repositories/adapters, imports, architecture checks, tests, graph, memory, and validation freshness.
- Accept, reject, or mark not verified any reused repository graph, project memory, layer convention, repository pattern, transaction pattern, exception mapping, or enforcement result.
- Identify presentation, application, domain, and infrastructure elements.
- Confirm controllers or handlers do not own core business decisions.
- Confirm domain code has no infrastructure or framework dependency.
- Define application service orchestration and transaction scope.
- Define validation, authorization, and error mapping boundaries.
- Define repository or adapter contracts used by application or domain code.
- Define infrastructure exception mapping at adapter boundaries.
- Identify any deliberate layer exception, owner, expiry/review trigger, and containment test.
- Confirm core behavior can be unit tested without infrastructure.
- Add dependency checks when the repository supports them.
- Map every changed entry point, use case, domain rule, repository interface, adapter, transaction boundary, exception mapping, dependency rule, and enforcement check to validation evidence or residual risk.
- Define handoff boundaries to module-boundary, service orchestration, domain invariant, repository/persistence, transaction consistency, architecture style, and quality/test owners.
