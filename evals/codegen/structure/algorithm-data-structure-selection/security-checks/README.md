# Security Checks

## Threat Surface

Large-input algorithms can create denial-of-service risk when unbounded user or provider data drives CPU, memory, or disk use.

## Required Checks

- Memory budget and batch size prevent untrusted load-all inputs.
- Probabilistic structures do not silently drop security-relevant exactness.
- Logs and benchmark artifacts avoid provider secrets and account PII.

## Rejection Cases

- Reject unbounded load-all processing for external input.
- Fail when nested scans can be triggered as a denial-of-service path.
- Reject approximate matching that changes financial or permission outcomes.
