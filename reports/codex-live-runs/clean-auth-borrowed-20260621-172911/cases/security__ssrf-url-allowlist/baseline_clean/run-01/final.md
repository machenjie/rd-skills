Implemented the SSRF allowlist hardening.

Files changed:
- `app.py`: centralized URL/network policy, exact HTTPS host allowlist, port canonicalization, DNS resolution before fetch, public IP enforcement, metadata/private/link-local/loopback denial, redirect revalidation, bounded fetch arguments, safe client errors.
- `tests/test_fetch_preview_security.py`: standard-library unit tests for allowed fetches, unsafe hosts/ports/parsing, private and metadata addresses, DNS failure, redirect denial/revalidation, timeout/fetch failure safety.
- `setup.sh`: made harness root discovery robust for this nested benchmark path.

Validation:
- `bash setup.sh` -> passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` -> 7 tests passed.
- `python3 -m py_compile app.py tests/test_fetch_preview_security.py` -> passed.
- `git diff --check` -> passed.
- `bash ../test-suite/run.sh` -> could not run: `../test-suite/run.sh` is absent in this isolated run tree.
- `bash ../security-checks/run.sh` -> could not run: `../security-checks/run.sh` is absent in this isolated run tree.

Reuse / placement evidence:
- Kept the existing `fetch_preview(url, http_get, resolver, logger=None, max_redirects=...)` service boundary and injectable `http_get`/`resolver`.
- Centralized policy in `_validate_fetch_url` inside `app.py`, rather than scattering checks around redirect handling.
- Tests are local deterministic checks under `tests/`, with no network dependency.

Residual risk:
- The default allowlist is intentionally narrow: `preview.example.com` on HTTPS port 443 only. Additional production preview domains would need to be explicitly passed via `allowed_hosts`.
- DNS is validated immediately before each injected fetch, but a real HTTP client would still need to avoid independently re-resolving to a different address unless it is wired to the validated resolution.