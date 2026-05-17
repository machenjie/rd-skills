# Example Output

Release strategy: Rolling deployment with feature flag disabled by default.

Prerequisites: Migration adds nullable column and completes in staging.

Validation: Contract tests pass, staging smoke archive flow succeeds, dashboard shows no elevated errors.

Rollback: Disable flag first; rollback service if errors persist. Leave additive column in place.

Post-release: Watch archive failure rate and search indexing lag for two hours.
