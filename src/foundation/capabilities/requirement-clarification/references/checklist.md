# Requirement Clarification Checklist

- Select the mode: ambiguity triage, authority decision gap, stakeholder conflict, evidence freshness check, partial proceed decision, or bug/incident intake.
- Record request source, exact requested behavior, stakeholder source, and any solution-first framing.
- Separate verified current facts from interpretations, stakeholder claims, repository inspection leads, prior task evidence, previous execution results, and guesses.
- Inspect current source/docs/tests/generated artifacts/reports when prior source or task evidence evidence is used; mark stale or unverified evidence explicitly.
- Classify each gap as blocking, non-blocking, safe engineering assumption, explicit stakeholder assumption, unsafe assumption rejected, or verified fact.
- Treat auth, tenant, money, compliance, data loss, migration, rollback, public contract, privacy, and irreversible decisions as blocking unless authority approves a bounded safe default.
- For a blocking unknown, record the exact question, blocked decision or acceptance item, required answer or decision shape, and accountable authority or explicit missing owner. Add category when it changes routing, a due or resume trigger for deferred or partial proceed, and a downstream Skill or owner when resolution crosses ownership.
- Before classifying an unknown as non-blocking, define a bounded safe default, isolation method, follow-up owner, expiration or reopening trigger, and validation or not-present check; otherwise classify it as blocking.
- Before classifying an assumption as safe for the current slice, document reversibility, supporting repository convention, and testability. Document why it does not decide product, security, legal, or other owner-held authority. Otherwise route it as an unresolved gap.
- For every stakeholder assumption, record source, verification needed, and what breaks if it is false.
- When clarification rejects an unsafe task-local assumption, retain the tempting shortcut, unacceptable risk, and exact evidence or owner response needed to reopen it.
- Decide `block`, `proceed`, or `partial proceed`; justify the decision with evidence, not preference.
- If partially proceeding, record surfaces that can proceed, surfaces that must wait, forbidden assumptions or artifacts, plus the review boundary.
- Map each question, assumption, evidence claim, safe default, and forbidden scope item to validation, review check, owner response, or residual risk.
- Record handoff capability, evidence limits, rollback/reversal note for assumptions, residual-risk owner, and final validation freshness.
