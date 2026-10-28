# Visual Reference Reconstruction

**Load when:** Screenshot, mockup, or reference-image implementation requires visual fidelity or matching the supplied reference.

**Do not load when:** No visual reference is supplied, or visual polish and redesign do not require matching one.

## Evidence And Decomposition

- Treat the supplied reference as visual evidence, not as product or runtime authority.
- Decompose visible page regions; treat inferred component boundaries as hypotheses to map onto the existing implementation.
- Infer layout geometry, spacing, typography, color, surfaces, and asset relationships from visible evidence.
- Mark ambiguous inferences instead of presenting them as observed facts; static images do not establish hidden interactions, source component structure, or responsive rules.
- Map the result to existing repository tokens, components, and design-system rules.

## Implementation Boundaries

- Apply priorities in this order: `repository/source authority > behavior correctness > security/accessibility > performance > existing design system > explicit reference fidelity > visual-quality heuristic`.
- Preserve repository architecture, semantic structure, real-content needs, and responsive behavior instead of distorting them for pixel imitation.
- For states and viewports absent from the reference, follow established project behavior and resolve only unknowns that affect a material implementation decision.
- Preserve security, accessibility, performance, and behavior contracts.
- Reuse existing components and tokens without bypassing or duplicating them.
- Avoid unnecessary dependencies or abstractions and valueless DOM/CSS complexity.

## Example: Shared Layout Drift

- If the page looks uniformly cramped and headings wrap differently, inspect container constraints, column proportions, and the actual font or fallback font before adjusting individual gaps.
- A shared constraint or font mismatch can shift many regions at once. Correct the identified cause with existing layout and typography rules, then address remaining local spacing differences.
- Avoid per-element offsets or hardcoded positioning that compensate for a common cause; they can match one image while breaking longer content or another viewport.
- Use this ordering when the observed mismatch spans regions; an isolated, understood spacing issue can remain a local change.

## Comparison And Proof

- Compare the final implementation with the reference at representative states and viewports.
- Record material mismatches and accepted fidelity tradeoffs.
- Record interaction, responsive behavior, accessibility, and runtime behavior as unproven by static image evidence.

## Required Output

- **Selected approach:** evidence decomposition, repository reuse, and accepted fidelity decisions.
- **Validation plan:** comparison states, viewports, tools, and mismatch handling.
- **Proof limit:** properties inferred or not provable from the static reference.
