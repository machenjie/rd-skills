No severity findings in the final review.

Files changed:
- `app.py`
- `tests/test_app.py`

Implemented:
- Centralized URL fetch policy in `app.py`.
- Exact HTTPS allowlist for `preview.example.com`.
- Canonical scheme/host/port handling before fetch.
- DNS resolution validation before each outbound request.
- Denial of loopback, private, link-local, IPv4-mapped loopback, and metadata addresses.
- Redirect revalidation before continuing a redirect chain.
- Bounded `http_get(..., timeout_seconds=2.0, max_bytes=65536)`.
- Generic client-safe denial errors that do not echo internal URLs, IPs, resolver details, or timeout internals.

Validation:
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` -> passed, 10 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile app.py tests/test_app.py` -> passed.
- `git diff --check -- app.py tests/test_app.py` -> passed.
- `bash setup.sh` -> failed: missing `scripts/codegen_benchmark_harness.py` under the computed isolated run root.
- `bash ../test-suite/run.sh` -> failed: file not found.
- `bash ../security-checks/run.sh` -> failed: file not found.

Reuse / placement evidence:
- Reused existing `app.py` ownership because `fetch_preview`, `HTTPResponse`, `PreviewResult`, `http_get`, and `resolver` seams already live there.
- Added tests under `tests/`, which README explicitly allows.
- Rejected new dependencies, network-backed tests, shared utilities, and private-helper-only tests.

Review / automatic failure check:
- Same-pattern scan found the old prefix host check removed.
- Denial error no longer contains the submitted URL.
- Generated `__pycache__` artifacts were removed.
- Remaining untracked `.agents/` and `.changeforge/` were present as benchmark/context files and were not modified.

Residual risk:
- Required benchmark runner scripts are unavailable in this isolated checkout, so full benchmark/security-suite evidence is not obtainable here.
- Real production SSRF hardening still depends on the injected HTTP client honoring the validated destination, timeout, and size contract.

```yaml
changeforge_route:
  route_id: ssrf-url-allowlist-backend-security
  complexity: L2-single-module-security-change
  risk_level: high
  selected_skills:
    - backend-change-builder
    - integration-change-builder
    - security-privacy-gate
    - reliability-observability-gate
    - quality-test-gate
  selected_capabilities:
    - input-validation
    - web-security
    - implementation-structure-design
    - failure-contract-design
    - unit-testing
    - integration-testing
    - agent-tool-permission-sandbox
    - plan-execution-consistency
  required_quality_gates:
    - security gate
    - reliability gate
    - quality-test gate
    - execution discipline gate
```

Rollback note: revert `app.py` and remove `tests/test_app.py`; no external state was changed.