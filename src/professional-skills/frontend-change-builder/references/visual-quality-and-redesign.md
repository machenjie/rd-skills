# Visual Quality And Redesign

**Load when:** The user explicitly requests visual polish or redesign, or hierarchy, typography, spacing, density, or composition is an acceptance target.

**Do not load when:** The frontend task is ordinary behavior work without a visual-quality acceptance target, or reference fidelity alone defines the visual goal.

## Decision Order

- Apply priorities in this order: `repository/source authority > behavior correctness > security/accessibility > performance > existing design system > explicit reference fidelity > visual-quality heuristic`.

## Visual Method

- Inspect the current page, components, and design system before choosing changes.
- Derive the visual direction from the product, user, scenario, existing design, and accepted goal.
- Check the dimensions implicated by the accepted goal or observed gap: hierarchy, typography, spacing, density, composition, geometry, color, motion, and media.
- Limit generic AI visual patterns to diagnostic evidence without converting them into binding rules.
- Prefer local repairs that address the accepted visual gap.
- Do not rewrite an existing implementation only for aesthetic preference.
- Check whole-page visual consistency after the changes.

## Example: An Unclear Save Action

- A settings page's Save action is easy to miss. Size alone does not explain the problem: inspect its grouping and position, its emphasis relative to secondary actions, and competing primary actions.
- If placement or emphasis causes the gap, adjust grouping, position, or emphasis through existing components and tokens; enlarging the button or rebuilding the page may leave the cause intact.
- For frequent data-scanning tasks, preserve useful density. More whitespace or larger headings can make comparison harder; use them only when they address the actual gap.
- This example connects symptom, cause, and local repair; it is not a mandatory redesign sequence for every change.

## Engineering Boundaries

- Preserve behavior, accessibility, security, performance, and existing design-system contracts.
- Reuse existing components and tokens without bypassing or duplicating them.
- Avoid unnecessary dependencies or abstractions and valueless DOM/CSS complexity.
- Do not prescribe fixed fonts, colors, radii, layouts, card patterns, asymmetry, texture/noise/glass, animation, gradients, or a "premium" style.

## Required Output

- **Selected approach:** derived direction, reused surfaces, local changes, and validation target.
- **Residual risk:** unverified states, viewports, media, motion, or consistency limits.
