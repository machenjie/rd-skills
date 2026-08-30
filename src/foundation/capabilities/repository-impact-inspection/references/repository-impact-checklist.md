# Repository Impact Checklist

- Start only after `repository-context-map` has identified source-of-truth, candidate-owner, and change-surface candidates; return there when any remains unknown.
- Read the candidate owner and its adjacent implementation and tests without choosing or rejecting a placement.
- Search callers, imports, schema or configuration keys, docs, and generated markers.
- Classify an exact locator from a user, AI, Brief, Review, log, or search result only after a direct current-source read; precision alone does not prove ownership.
- Label each path as owner, consumer, test, configuration, documentation, generated
  output, or unknown.
- Confirm the generated-source boundary before proposing edits.
- Permit multiple necessary enforcement points when each is proved; do not force a unique owner.
- Treat zero static references as a Proof Limit when dynamic dispatch, registries, reflection, DI, plugins, generated edges, or FFI can retain consumers.
- Return direct impact evidence, inferences, affected consumers and contracts,
  validation boundaries, uninspected scope, and residual risk.
- Stop when further search cannot change the bounded impact, validation boundary, or material risk; leave placement decisions to the owning analysis.
