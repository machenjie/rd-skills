---
name: powershell-professional-usage
description: "PowerShell pipeline, native, error, remoting, provider, and repeat-run decisions."
---

# powershell-professional-usage

## Registry Trigger

**Use when**

- PowerShell pipeline/native/error/encoding/remoting/provider/repeat-run semantics

**Do not use when**

- mention-only, POSIX, or Windows-policy work

## Skill Role

Own PowerShell semantics for the actual edition/host; leave adjacent concerns to their owners.

## High-Value Rules

- Define caller authority.
- Define target authority.
- Bind runtime, remoting, provider, convergence, cleanup, repeat-run, and recovery semantics to both authorities.
- Define remoting, provider, and administration behavior with cleanup and repeat-run safety.
- Preserve convergence and recovery evidence through the named Reference.

## Anti-Patterns

- Local success substituted for evidence of the powershell professional usage contract.

## Stop Conditions

- Stop on unresolved target/host/identity/remote/provider/secret/state/recovery.

## Output Contract

- PowerShell decision with pipeline and target-state paths error native encoding remoting credentials provider module version first and repeat outcomes evidence limits routes and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [pipeline error and native contracts](references/pipeline-error-and-native-contracts.md) | targeted | Pipeline binding errors native arguments/exits streams or encoding changes | Object error native-process stream and encoding behavior remain unchanged | task-agent, review-agent, analysis-agent | decision-record, residual-risk |
| [remoting provider and administration contracts](references/remoting-provider-and-administration-contracts.md) | targeted | Remoting credentials providers modules policy privilege or idempotent administration changes | No remote secret provider module or target-state boundary changes | task-agent, review-agent, analysis-agent | selected-approach, proof-limit, residual-risk |
