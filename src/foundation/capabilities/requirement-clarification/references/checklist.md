# Requirement Clarification Checklist

- Select the mode: ambiguity triage, authority decision gap, stakeholder conflict, evidence freshness check, partial proceed decision, or bug/incident intake.
- Record request source, exact requested behavior, stakeholder source, and any solution-first framing.
- Separate verified current facts from interpretations, stakeholder claims, repository graph leads, project memory, previous execution results, and guesses.
- Inspect current source/docs/tests/generated artifacts/reports when graph or memory evidence is used; mark stale or unverified evidence explicitly.
- Classify each gap as blocking, non-blocking, safe engineering assumption, explicit stakeholder assumption, unsafe assumption rejected, or verified fact.
- Treat auth, tenant, money, compliance, data loss, migration, rollback, public contract, privacy, and irreversible decisions as blocking unless authority approves a bounded safe default.
- For every blocking unknown, name the question, category, owner, decision shape, due date or trigger, why it blocks, and downstream gate.
- For every non-blocking unknown, define safe default, isolation method, follow-up owner, expiration/trigger, and validation or not-present check.
- For every safe assumption, state why it is reversible, conventional in this repo, testable, and not authority-owned.
- For every stakeholder assumption, record source, verification needed, and what breaks if it is false.
- For every rejected unsafe assumption, name the tempting shortcut, risk, and evidence or owner response required.
- Decide `block`, `proceed`, or `partial proceed`; justify the decision with evidence, not preference.
- If partially proceeding, list can-implement-now surfaces, must-wait surfaces, forbidden assumptions/artifacts, and review boundary.
- Map each question, assumption, evidence claim, safe default, and forbidden scope item to validation, review check, owner response, or residual risk.
- Record handoff capability, evidence limits, rollback/reversal note for assumptions, residual-risk owner, and final validation freshness.
