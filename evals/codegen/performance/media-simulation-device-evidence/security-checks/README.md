# Security Checks

## Threat Surface

All inputs and effects are in-memory records. The fixture has no production, device, network, or file mutation authority.

## Required Checks

Reject missing completion and stale epochs before host use. Require track cleanup on terminal paths and bounded catch-up under the supplied policy.

## Rejection Cases

Recorded submission cannot authorize a host read. These checks do not establish real driver safety, sandboxing, codec robustness, or resource capacity.
