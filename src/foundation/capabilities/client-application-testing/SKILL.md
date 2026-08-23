---
name: client-application-testing
description: "`analysis-agent`/`task-agent`/`review-agent`: test installed-client lifecycle, permission, activation, installation, device, or accessibility behavior; skip general quality."
---

# client-application-testing

## Registry Trigger

**Use when**

- Changed installed-client behavior needs proof across application lifecycle, operating-system integration, installation state, device configuration, or accessibility settings.

**Do not use when**

- The work is a pure backend, API-contract, component-only browser, or general test-portfolio decision without an installed-client risk.

## Skill Role

Own client interruption, artifact, environment, oracle, and cleanup decisions; exclude general strategy, release, platform, and accessibility-conformance decisions.

## High-Value Rules

- Derive the smallest client matrix for the named failure.
- For the named client failure, bind its oracle to clean state and a release-equivalent artifact.
- Select `client-test-matrix.md` only when client dimensions compete.

## Anti-Patterns

- Local success substituted for evidence of the client application testing contract.

## Stop Conditions

Stop without the matrix, artifact, OS control, or cleanup authority. Record skipped hardware, versions, accessibility, and destructive-install states as limits.

## Output Contract

- client-test decision with risk matrix interruption and activation cases permission and connectivity transitions artifact and data states environment coverage oracles cleanup unavailable scope and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [client test matrix](references/client-test-matrix.md) | targeted | Lifecycle permission activation upgrade device locale scaling assistive-technology or resource-pressure coverage spans several dimensions | One local test already exercises the complete changed client failure mechanism | analysis-agent, task-agent, review-agent | validation-plan, residual-risk |
