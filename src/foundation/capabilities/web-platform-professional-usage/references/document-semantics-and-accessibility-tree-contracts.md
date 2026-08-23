# Document Semantics and Accessibility Tree Contracts

Use this Reference only for the named document-semantics-and-accessibility-tree-contracts decision.

## Decision Rules

- Select HTML elements from content meaning, native behavior, form or navigation role, and supported elements before adding roles or scripted behavior.
- Bind DOM ownership to the node tree, shadow boundaries, mutation owner, and listener lifetime, using the narrowest stable owner.
- Verify native role, name, state, focusability, hidden state, relationships, accessibility-tree representation, and interaction rather than DOM shape alone.
- HTML and DOM are Living Standards; ARIA mappings explain exposure but do not make custom DOM equivalent to native HTML.

Reject generic elements that assume ARIA restores native behavior. Return native semantics, DOM owner, exposed tree, target engines, and proof limits.
