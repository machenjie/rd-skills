# Security Checks

## Threat Surface

This benchmark has no external input, auth, secret, network, or database
surface. The security concern is accidental expansion of public surface.

## Required Checks

Review that the implementation does not add a new public service, registry,
config switch, or shared utility that would widen future trust boundaries.

## Rejection Cases

Reject implementations that add public APIs for one local label rule or claim
minimal validation as evidence for unreviewed security-sensitive behavior.
