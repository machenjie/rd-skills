# Routing Navigation Evidence Patterns

Use this reference when route closure depends on proving current route behavior, backend-authorization limits, generated-link/template freshness, public URL migration safety, prior source or task evidence freshness, or route-change-to-validation mapping. Keep `SKILL.md` for route selection and output shape; load this file only for concrete evidence closure.

## Claim To Evidence Map

| Claim | Minimum evidence | Does not prove |
| --- | --- | --- |
| Route table is current | Router config, file-based route tree, page/layout/loader files, and route owner inspected after final edit. | Generated links, email templates, partner URLs, or SEO indexes are safe unless inspected. |
| Guard is security-correct | Frontend guard classification plus backend/API 401/403 denial evidence or explicit not-verified handoff. | Frontend-only protection is sufficient security control. |
| Redirect is safe | Same-origin `returnTo` validation, external URL rejection, safe fallback, loop-depth map, and browser-history proof. | Every historical redirect or third-party callback remains safe. |
| Deep/stale link recovers | Allowed, unauthenticated, unauthorized, unavailable, invalid-param, deleted/archived, never-existed, and dependency-failure branches mapped to tests or manual checks. | Live bookmarks, emails, notifications, and search indexes are all covered. |
| Public URL migration is compatible | Old/new route map, caller inventory, redirect/deprecation decision, telemetry or link-crawler proof, rollback note. | Unknown partner links or SEO cache behavior without external evidence. |
| Generated-link/template evidence is fresh | Link builders, breadcrumbs, docs/sitemap, email/notification templates, and generated outputs inspected or regenerated after final route edit. | Runtime analytics or production dead-link rate. |

## Route Validation Map

```yaml
route_change_to_validation_map:
  route_or_surface: ""
  changed_behavior: ""
  source_evidence: []
  backend_auth_evidence: ""
  generated_link_or_template_evidence: []
  validation:
    command_or_manual_check: ""
    covers:
      - guard_classification
      - deep_link_state
      - redirect_history
      - parameter_validation
      - public_url_compatibility
  evidence_limits: []
  residual_risk_owner: ""
```

## Closure Checks

- Treat repository inspection, prior task evidence, analytics, support reports, and generated docs as selectors until current route source confirms them.
- Name any uninspected backend auth, generated link, email, notification, partner, SEO, browser, or analytics surface as residual risk.
- Separate dry-run/manual browser evidence from automated route tests and live production evidence.
- Do not claim route migration safety unless old valid links, stale links, generated links, and rollback behavior are all mapped to evidence or explicit residual risk.
