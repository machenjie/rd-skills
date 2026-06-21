Implemented SSRF allowlist validation.

Files changed:
- [app.py](<local-path> centralized URL policy, exact HTTPS origin allowlist, canonical host/port handling, DNS address denial via `ipaddress`, redirect revalidation, bounded fetch options, safe denial logging/errors.
- [tests/test_url_policy.py](<local-path> unit coverage for allowed fetches, prefix-bypass rejection, private/metadata address denial, redirect denial before next fetch, DNS/parse/timeout fail-closed paths.

Validation:
- `python3 -m unittest discover -s tests -v` passed: 5 tests OK.
- `CHANGEFORGE_CODEGEN_ROOT=<local-path> bash setup.sh` passed.
- Canonical benchmark test suite passed: 2 tests OK.
- Canonical security checks passed: 3 tests OK.
- Exact `bash setup.sh` failed initially because the copied run computed a missing harness path.
- Exact `bash ../test-suite/run.sh` and `bash ../security-checks/run.sh` failed because those sibling directories are absent in this isolated run copy.

Reuse/placement evidence:
- Kept the public `fetch_preview(url, http_get, resolver, logger=None, max_redirects=3)` boundary.
- Reused injectable `http_get` and `resolver` seams for deterministic validation and tests.
- `rg` scan found no remaining `startswith` allowlist logic or URL-bearing denial log pattern.

Residual risk:
- The network layer is still represented by injected `http_get`; this policy validates resolver output before fetch, but a real HTTP client should also bind/connect consistently with the validated resolution to fully mitigate DNS rebinding.