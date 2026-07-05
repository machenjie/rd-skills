# Security Checks

## Threat Surface

The security surface is package supply chain, lockfile churn, and timezone bugs
that can corrupt downstream reports.

## Required Checks

Reject new dependencies unless the dependency decision includes transitive
impact, license compatibility, vulnerability status, and install-script review
where applicable.

## Rejection Cases

Reject convenience date packages, unreviewed lockfile updates, and local
timezone formatting that changes behavior across environments.
