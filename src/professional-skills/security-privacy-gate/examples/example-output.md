# Example Output

Decision: Block until object-level authorization is enforced.

Finding: Archive endpoint checks authentication but not project ownership.

Risk: High because any authenticated user could alter another tenant's project.

Required fix: Verify tenant and owner or admin role server-side before state transition.

Evidence required: Authorization matrix integration tests and audit log verification.
