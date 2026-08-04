# Repository Impact Checklist

- Start only after `repository-context-map` has identified source-of-truth, candidate-owner, and change-surface candidates; return there when any remains unknown.
- Read the candidate owner and its adjacent implementation and tests without choosing or rejecting a placement.
- Search callers, imports, schema or configuration keys, docs, and generated markers.
- Label each path as owner, consumer, test, configuration, documentation, generated
  output, or unknown.
- Confirm the generated-source boundary before proposing edits.
- Return direct impact evidence, inferences, affected consumers and contracts,
  validation boundaries, uninspected scope, and residual risk.
- Stop when further search cannot change the bounded impact, validation boundary, or material risk; leave placement decisions to the owning analysis.
