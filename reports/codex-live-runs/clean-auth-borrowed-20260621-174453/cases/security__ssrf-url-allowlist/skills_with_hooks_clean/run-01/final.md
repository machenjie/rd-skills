Implemented the SSRF allowlist hardening.

Files changed:
- [app.py](<local-path> centralized URL/network policy, exact HTTPS host allowlist, DNS/IP denial checks, redirect revalidation, bounded fetch arguments, safe client errors.
- [tests/test_fetch_preview_security.py](<local-path> unit coverage for allowed fetches, prefix-host bypass, private IP denial, redirect SSRF, DNS failure, malformed URLs, timeout handling.
- [IMPLEMENTATION_NOTE.md](<local-path> tradeoffs and residual risk.

Validation:
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` passed: 8 tests.
- `python3 -m py_compile app.py tests/test_fetch_preview_security.py` passed.
- `bash setup.sh` failed because `scripts/codegen_benchmark_harness.py` is missing from the isolated copy.
- `bash ../test-suite/run.sh` failed because the script does not exist.
- `bash ../security-checks/run.sh` failed because the script does not exist.

Reuse/placement evidence: same-pattern scan found only `fetch_preview`/resolver/http_get in `app.py`, so the policy was kept in that service module instead of adding a new abstraction. Existing injectable `http_get` and `resolver` seams were reused for deterministic tests.

Residual risk: DNS rebinding remains possible if a production HTTP client resolves the hostname again instead of connecting to the validated address. Benchmark-level validation is also incomplete because the required external scripts are absent. ChangeForge route used: `backend-change-builder`, reviewed by `security-privacy-gate` and `quality-test-gate`; no docs-only or network-only workaround was used.