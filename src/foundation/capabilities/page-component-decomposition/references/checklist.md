# Page Component Decomposition Checklist

- Identify the page or screen owner and its orchestration responsibilities.
- List child components and the single primary responsibility of each.
- Assign state ownership and reset behavior to the nearest correct owner.
- Separate presentational rendering from data fetching, route context, and side effects.
- Confirm shared components have stable contracts and real reuse pressure.
- Check for giant components that mix workflow, data, validation, and rendering.
- Check for premature micro-components that add indirection without clarity.
- Define inputs, outputs, callbacks, and side effects for each component.
- Cover loading, empty, error, permission, disabled, and success states where relevant.
- Identify the component-level and flow-level tests that prove the decomposition works.
