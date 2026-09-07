# Layout, Paint, and Compositing Contracts

Use this Reference only for the named layout-paint-and-compositing-contracts decision.

## Decision Rules

- Diagnose formatting context, containing block, intrinsic size, overflow, and writing mode before paint or compositing changes.
- Assign stacking-context creators, paint order, clipping, transforms, and positioned descendants to their responsible context instead of escalating arbitrary `z-index` values.
- Treat changed pixels, animation properties, layer behavior, memory, and promotion as engine-dependent and measurement-bound.
- CSS defines formatting, containment, positioning, and paint order; engine documentation supplies diagnostic stages, not portable optimization guarantees.

Return the selected rendering approach, target-engine validation, measured evidence, draft limits, and non-inferences.
