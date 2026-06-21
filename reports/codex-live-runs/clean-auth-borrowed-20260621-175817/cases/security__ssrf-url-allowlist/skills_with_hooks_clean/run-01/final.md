Implemented the SSRF allowlist change.

Files changed:
- [app.py](<local-path>
- [tests/test_ssrf_allowlist.py](<local-path>
- [setup.sh](<local-path>

What changed:
- Centralized URL fetch policy in `NetworkPolicy`.
- Exact HTTPS host allowlist: `preview.example.com`.
- Canonicalizes scheme, host, port, and resolver output before fetch.
- Rejects loopback, private, link-local, reserved, multicast, unspecified, and malformed resolved addresses.
- Revalidates every redirect target before the next outbound request.
- Keeps bounded `timeout_seconds=2.0` and `max_bytes=65536`.
- Returns generic client-safe denial errors without echoing internal URLs or addresses.
- Made `setup.sh` locate the benchmark harness upward so `bash setup.sh` works in this isolated nesting.

Validation:
- `bash setup.sh` passed: `setup: run-01 starter repo is installable`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` passed: 6 tests OK.
- `bash ../test-suite/run.sh` could not run: `No such file or directory`.
- `bash ../security-checks/run.sh` could not run: `No such file or directory`.

Reuse / placement evidence:
- Same-pattern scan found only `fetch_preview` in `app.py`; no existing validator/service package existed.
- Kept policy private and colocated in `app.py` to avoid a new module for a single service boundary.
- Tests exercise public `fetch_preview` behavior through the existing injectable `http_get` and `resolver` seams.

Residual risk:
- The supplied sibling benchmark scripts are absent from this isolated copy, so only local tests and setup were verified.
- DNS rebinding prevention is limited to the injectable resolver validation boundary; a production HTTP client should also pin/connect through the validated address or enforce egress policy.

changeforge_route: backend-change-builder + security-privacy-gate + quality-test-gate; capabilities: input-validation, web-security, implementation-structure-design, minimal-correct-implementation, regression-testing.