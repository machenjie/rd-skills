# Example Output

```markdown
## Information Architecture Plan

Mode selected: Navigation hierarchy and role visibility.

IA scope: Finance reporting module; excludes export job backend design and visual table layout.

Source evidence: Current left navigation, finance analyst role list, compliance role notes, export list route, and prior support handoff pattern inspected. Project memory about "Account Export Jobs" rejected because current labels use reporting vocabulary.

Graph/memory/trajectory judgment:
- Accepted: existing Reports section remains the owner for export tasks.
- Rejected: internal "Account Export Jobs" label.
- Not verified: live tree-test evidence and production analytics.

Primary task: Finance analyst reviews and exports monthly account data; compliance analyst audits export history.

Structure:
- Reports
  - Monthly Exports
    - Export list
    - Export detail
    - Create export
  - Audit Exports
    - Audit export list

Navigation rules:
- Finance users see Monthly Exports.
- Compliance users also see Audit Exports.
- Support users see export metadata from account detail but no file download.
- Direct links to Audit Exports show locked access for finance users with a request-access CTA; confidential audit details remain hidden.

Label decision:
- Use "Monthly Exports" instead of "Account Export Jobs" because the task is reporting, not job management.

Empty and unavailable states:
- No monthly exports: explain that generated exports appear here and offer "Create export."
- Filtered-empty audit results: offer "Clear filters."
- Export archived: show unavailable state with link back to Monthly Exports.

Cross-module handoff:
- Account detail links to export metadata with account breadcrumb preserved and back navigation returning to the account.

Changed IA to validation map:
- Monthly Exports label: vocabulary review with finance lead.
- Audit Exports visibility: role matrix review and direct-link behavior test.
- Account handoff: route/back-navigation test or residual risk if route implementation is not in scope.

Validation obligations:
- Tree test target: finance and compliance analysts find Monthly Exports directly on primary tasks.
- Role visibility review owner: compliance lead signs off locked vs hidden audit destinations.
- Route validation freshness: direct-link behavior test must run after final route/nav label edit.
- Not-run consequence: live analytics and browser validation remain residual release risk.

Handoff boundaries:
- `routing-navigation-design` owns URL guard behavior.
- `permission-boundary-modeling` owns authorization policy.
- `user-flow-modeling` owns multi-step export creation.

Evidence limits:
- No live card sort, tree test, production analytics, or real browser validation was run.
```
