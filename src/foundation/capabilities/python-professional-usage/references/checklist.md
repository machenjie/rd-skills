# Python Professional Usage Checklist

- Use type hints to protect public module and service boundaries.
- Validate external inputs at runtime.
- Keep environments and package installs reproducible.
- Review async/sync boundaries and avoid event-loop blocking.
- Assess GIL impact for CPU-heavy work.
- Keep pytest fixtures deterministic, isolated, and cleanup-safe.
- Make operational scripts idempotent or guarded.
- Run relevant type, lint, unit, and integration checks.
