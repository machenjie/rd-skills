# Event Dispatch and Default Action Contracts

Use this Reference only for the named event-dispatch-and-default-action-contracts decision.

## Decision Rules

- Trace capture, target, bubble, composed path, shadow retargeting, cancellation, default action, and listener lifetime through the actual DOM tree.
- Preserve browser default behavior unless the product explicitly replaces it and the owner, failure, cleanup, and supported-engine behavior are proven.
- Do not infer event, focus, visual, or accessibility-tree order from DOM order alone.
- Bind conclusions to current HTML and DOM algorithms plus target-engine evidence.

Return the event path, cancellation and default-action decision, failure behavior, and proof limits.
