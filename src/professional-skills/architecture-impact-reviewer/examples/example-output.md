# Example Output

Decision: Keep archival policy inside the existing project domain service.

Rejected alternative: New archival microservice. It adds network dependency and ownership overhead without independent scaling need.

Boundary impact: No service boundary change.

Tradeoff: Domain service gains one policy branch, but consistency remains local.

Documentation: Add short ADR note because future archival states are likely.
