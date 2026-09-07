# Accessibility Closure Gates

Use this Reference only for the named accessibility-closure-gates decision.

## Decision Rules

- Bind keyboard behavior, focus, accessible name, role, live region, contrast, target size, and reduced motion to the accepted accessibility contract.
- Verify the changed keyboard path with automated and manual evidence; name the screenshot or report path and limits.
- Check affected content, focus, and recovery against their accepted behavior; keyboard evidence alone does not close those claims.
- Check analytics only when the changed interaction affects assigned instrumentation or its accepted event contract.
- Stop when a primary interaction lacks keyboard or screen-reader proof.
- Do not treat an inaccessible action with an added label as closed.

Return the accessibility gate decision, validation plan, and proof limits.
