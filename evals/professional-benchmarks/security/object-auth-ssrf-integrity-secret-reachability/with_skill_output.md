# Security release decision

Selected `security-privacy-gate` with `permission-boundary-modeling`, `web-security`, and `secret-configuration-security`.

The release is blocked. The reviewed risks are: tenant object ownership is not implied by authentication; redirect and DNS re-resolution can reach a private address; ambient-cookie mutation lacks cross-site request integrity; credentials can enter logs and build artifacts; and scanner severity lacks deployed reachability evidence.

Required proof is a cross-tenant denied-object test, a redirect-hop and post-resolution private-address test, a cross-site ambient-cookie negative test, a log and build-artifact credential scan, and deployed-version and reachable-call-path proof.

The handoff must include a release verdict with blocking findings, reviewed and unreviewed trust boundaries, repair owner and residual risk, and evidence limits and unproved claims. The endpoint owner must bind subject, tenant, and object authority; the fetch owner must re-check every redirect and resolved destination; the request boundary must establish cross-site integrity; and the build owner must remove and rotate exposed credentials before re-review.
