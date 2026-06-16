# Security Checks

## Threat Surface

The primary security risk is deleting or hiding behavior that protects billing,
authorization, or other sensitive decisions.

## Required Checks

Reject delete/shrink recommendations that touch security-sensitive logic without
caller search, behavior-preservation evidence, and regression coverage.

## Rejection Cases

Reject wrapper removals that hide authorization, error handling, audit logging,
or side-effect boundaries. Reject fewer-line changes that lose public behavior
or security evidence.
