# Design System Rules Checklist

- Select mode: existing component, variant/token, accessibility-critical, responsive/dense, or new component proposal.
- Inspect current design-system source, docs, stories, tokens, tests, and closest alternatives.
- Record repository graph, project memory, or execution trajectory evidence only when current source confirms it.
- Identify existing components and patterns to reuse.
- Define allowed variants and the product state each represents.
- Define forbidden variants, invalid prop combinations, and rejected visual-preference overrides.
- Reject one-off visual variants without behavioral need.
- Define component composition and ownership boundaries.
- Define accessibility requirements for labels, focus, keyboard, announcements, contrast, and target size.
- Define responsive behavior for dense, narrow, and wide contexts.
- Define content length, truncation, wrapping, and overflow rules.
- Identify invalid prop or state combinations.
- Justify new components with reuse and interaction evidence.
- Map every changed component, variant, token, state, breakpoint, and accessibility obligation to validation evidence or residual risk.
- Define review and test evidence for component consistency: Storybook, screenshots, axe, Lighthouse, keyboard path, screen reader, visual regression, or not-verified disclosure.
- Name handoff boundaries and evidence limits so design-system review is not over-claimed as implementation or full accessibility certification.
