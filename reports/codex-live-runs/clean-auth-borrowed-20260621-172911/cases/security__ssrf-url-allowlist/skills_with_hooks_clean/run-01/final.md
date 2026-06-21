Implemented SSRF URL fetch validation in the candidate repo.

**Files Changed**
- [app.py](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/clean-auth-borrowed-20260621-172911/cases/security__ssrf-url-allowlist/skills_with_hooks_clean/run-01/candidate/app.py): centralized allowlist/network policy, URL canonicalization, resolved-address denial, redirect revalidation, safe denial errors, timeout/fetch fail-closed handling, bounded response parsing.
- [tests/test_app.py](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/clean-auth-borrowed-20260621-172911/cases/security__ssrf-url-allowlist/skills_with_hooks_clean/run-01/candidate/tests/test_app.py): unit coverage for allowed fetch, host prefix rejection, private/loopback/link-local/metadata denial, redirect revalidation, DNS/timeout/fetch fail-closed paths.
- [tests/__init__.py](/Users/mcjxy/Projects/github/rd-skills/reports/codex-live-runs/clean-auth-borrowed-20260621-172911/cases/security__ssrf-url-allowlist/skills_with_hooks_clean/run-01/candidate/tests/__init__.py): enables default unittest discovery.

**Validation**
- `python3 -m unittest discover -v`: passed, 6 tests.
- `python3 -m py_compile app.py tests/test_app.py`: passed.
- `bash setup.sh`: failed because `scripts/codegen_benchmark_harness.py` is missing from the isolated benchmark root.
- `bash ../test-suite/run.sh`: failed, file not found.
- `bash ../security-checks/run.sh`: failed, file not found.

**Reuse / Placement Evidence**
- Reused the existing `fetch_preview(url, http_get, resolver, logger=None)` public boundary and injectable HTTP/resolver seams.
- Kept network policy in `app.py` because this starter repo has a single backend service module and no existing policy package.
- Same-pattern scan found only the existing vulnerable URL/redirect handling in `app.py`.

**Residual Risk**
- The injected `http_get` contract still owns the actual socket connection, so a production adapter should ensure it connects only to the validated resolved address set to fully close DNS-rebinding risk.
- Required benchmark harness scripts are absent in this isolated copy, so only local executable checks could be completed.

`changeforge_route`: backend security fix, L2/high risk, selected skills `change-forge-router`, `backend-change-builder`, `security-privacy-gate`, `quality-test-gate`; capabilities `input-validation`, `web-security`, `failure-contract-design`, `regression-testing`, `implementation-structure-design`.

`changeforge_stage_route`: implement -> validate -> review -> handoff complete, with benchmark-script availability as the only blocked evidence.