# Layered Architecture Design Checklist

- Identify presentation, application, domain, and infrastructure elements.
- Confirm controllers or handlers do not own core business decisions.
- Confirm domain code has no infrastructure or framework dependency.
- Define application service orchestration and transaction scope.
- Define validation, authorization, and error mapping boundaries.
- Define repository or adapter contracts used by application or domain code.
- Identify any deliberate layer exception and its owner.
- Confirm core behavior can be unit tested without infrastructure.
- Add dependency checks when the repository supports them.
