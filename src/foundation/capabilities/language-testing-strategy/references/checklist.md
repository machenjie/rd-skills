# Language Testing Strategy Checklist

- Identify language/runtime failure modes touched by the change.
- Map each risk to unit, integration, contract, property, concurrency, visual, or E2E coverage.
- Include boundary validation for dynamic or external inputs.
- Add race, sanitizer, fuzz, or stress checks where relevant.
- Verify fixtures and mocks are deterministic and cleanup-safe.
- Define CI commands and required evidence.
- Document untested risks and compensating controls.
- Align tests to acceptance criteria.
