# Activation Precision Evaluation

This generated report uses deterministic route activation fixtures. It measures resolver precision/recall for staged loading decisions; it is not live runtime pass-rate evidence.

## Summary

- Status: `pass`
- Cases: 6
- Passed: 6
- Failed: 0

| Metric | Value |
| --- | --- |
| `stage_accuracy` | `1.0` |
| `skill_precision` | `1.0` |
| `skill_recall` | `1.0` |
| `capability_precision` | `1.0` |
| `capability_recall` | `1.0` |
| `reference_precision` | `1.0` |
| `reference_recall` | `1.0` |
| `language_fp_rate` | `0.0` |
| `language_fn_rate` | `0.0` |
| `risk_surface_fp_rate` | `0.0` |
| `risk_surface_fn_rate` | `0.0` |
| `overroute_rate` | `0.0` |

## Cases

| Case | Status | Stage | Product Surfaces | Languages | Risks |
| --- | --- | --- | --- | --- | --- |
| `backend-conditional-planning` | `pass` | `implementation-planning` | backend-product | python | none |
| `frontend-tsx-no-backend` | `pass` | `implementation-planning` | frontend-product | typescript | none |
| `webhook-review-no-web3` | `pass` | `code-review` | external-integration, webhook | python | none |
| `backend-security-risk` | `pass` | `implementation-planning` | backend-product | python | security |
| `docs-release-handoff` | `pass` | `documentation-handoff` | documentation-only | none | delivery, documentation |
| `web3-wallet-no-webhook` | `pass` | `implementation-planning` | web3 | none | none |
