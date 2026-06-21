Implemented SSRF URL validation in the candidate repo.

Files changed:
- [app.py](<local-path> centralized URL policy, exact HTTPS host allowlist, DNS/IP denial checks, safe errors, bounded fetch, redirects disabled in urllib and revalidated in `fetch_preview`.
- [tests/test_app.py](<local-path> unit/integration coverage for allowed fetches, denied hosts/ports, private/link-local/metadata/loopback addresses, DNS/parse/timeout failures, and redirect revalidation.
- [tests/__init__.py](<local-path>
- [README.md](<local-path> implementation note and residual risk.

Validation:
- `python3 -m unittest discover -v` passed: 10 tests OK.
- `python3 -m py_compile app.py tests/test_app.py` passed.
- `bash setup.sh` failed because the expected harness file is absent: `scripts/codegen_benchmark_harness.py` not found.
- `bash ../test-suite/run.sh` failed: file not found.
- `bash ../security-checks/run.sh` failed: file not found.

Placement/reuse evidence: kept the existing `fetch_preview(url, http_get, resolver, logger=None)` public boundary and reused the injectable HTTP/resolver design for deterministic tests. Policy is centralized in `validate_preview_url`.

Residual risk: DNS rebinding remains possible unless the actual outbound connection is pinned to the already-validated resolved address or enforced by egress proxy/firewall policy.