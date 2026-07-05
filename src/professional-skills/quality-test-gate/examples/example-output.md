# Example Output

Test matrix:

- Unit: archive policy rejects invalid states.
- Integration: owner can archive; non-owner is forbidden.
- Contract: API response includes nullable `archived_at`.
- Migration: adding column is reversible at code level.
- E2E: owner archives project and active list updates.
- Manual: verify production-like smoke path in staging.

Residual risk: Search index lag requires monitoring after release.
