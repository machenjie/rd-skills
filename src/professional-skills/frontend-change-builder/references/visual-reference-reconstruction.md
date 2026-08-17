# Visual Reference Reconstruction

**Load when:** Screenshot, mockup, or reference-image implementation requires visual fidelity or matching the supplied reference.

**Do not load when:** No visual reference is supplied, or visual polish and redesign do not require matching one.

## Evidence And Decomposition

- Treat the supplied reference as visual evidence, not as product or runtime authority.
- Decompose it into page regions and component boundaries.
- Infer layout geometry, spacing, typography, color, surfaces, and asset relationships from visible evidence.
- Mark ambiguous inferences instead of presenting them as observed facts.
- Map the result to existing repository tokens, components, and design-system rules.

## Implementation Boundaries

- Apply priorities in this order: `repository/source authority > behavior correctness > security/accessibility > performance > existing design system > explicit reference fidelity > visual-quality heuristic`.
- Preserve repository architecture instead of distorting it for pixel imitation.
- Define responsive states that the reference does not show.
- Preserve security, accessibility, performance, and behavior contracts.
- Reuse existing components and tokens without bypassing or duplicating them.
- Avoid unnecessary dependencies or abstractions and valueless DOM/CSS complexity.

## Comparison And Proof

- Compare the final implementation with the reference at representative states and viewports.
- Record material mismatches and accepted fidelity tradeoffs.
- Record interaction, responsive behavior, accessibility, and runtime behavior as unproven by static image evidence.

## Required Output

- **Selected approach:** evidence decomposition, repository reuse, and accepted fidelity decisions.
- **Validation plan:** comparison states, viewports, tools, and mismatch handling.
- **Proof limit:** properties inferred or not provable from the static reference.
