---
name: powershell-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use for PowerShell pipeline, error, native, encoding, remoting, credential, provider, module, or idempotency decisions."
---

# powershell-professional-usage

## Registry Trigger

**Use when**

- PowerShell automation changes object-pipeline binding, terminating/non-terminating errors, native exit/argument behavior, encoding, remoting, credentials, providers, modules, or administrative idempotency.
- Edition/version, host, OS, module/provider, policy, or endpoint can change behavior beyond one successful run.

**Do not use when**

- PowerShell appears only in comments, examples, filenames, or unchanged generated output.
- The change is a POSIX shell script or only Windows registry/deployment policy with no PowerShell semantic decision.

## Skill Role

Own PowerShell pipeline, error, native, encoding, remoting, provider, module, and repeatable-administration semantics. Leave POSIX shell, Windows policy/deployment, and generic concerns to their owners.

## High-Value Rules

- Prove object-pipeline preservation, binding, enumeration, cardinality, and stream behavior through the final presentation or byte/text boundary.
- Classify terminating/non-terminating errors; set catch/`ErrorAction`, preserve error records, and define automation exit.
- For native commands, define argument tokens, stdout/stderr/bytes, `$LASTEXITCODE`, `$?`, accepted codes, timeout, cancellation, and redaction.
- Define file/process encodings against Windows PowerShell 5.1 and PowerShell 7 behavior.
- For remoting, define endpoint, local/remote evaluation, serialization loss, session lifetime, fan-out, policy, authentication, and second hop.
- Obtain secrets from an approved provider, minimize scope, never stringify/log material, and define renewal/revocation failure.
- Treat provider paths as provider-specific data stores; prove provider availability, dynamic parameters, literal/wildcard semantics, item type, permissions, and rollback.
- Make administration convergent: inspect state, compute change, use `ShouldProcess` where destructive, verify post-state, and prove a safe second run.

## Anti-Patterns

- Formatted text is piped as data, implicit enumeration changes cardinality, or a pipeline success is inferred from visible output.
- `try/catch` is assumed to catch non-terminating errors, or `$?` is assumed to replace a native exit-code contract.
- Interpolated commands, default encoding, or implicit remoting serialization is treated as portable across hosts/editions.
- A successful first run, `-Force`, or `WhatIf` output is treated as idempotency, rollback, least privilege, or target-state proof.

## Stop Conditions

- Stop until behavior-controlling edition, host, OS, module/provider, language mode, and endpoint are known.
- Route POSIX pipelines to `shell-cli-professional-usage` and Windows registry/deployment, policy, signing, or packaging to their domain owner.
- Route authorization, secret storage, destructive approval, release, logging, and tests to their owners.
- Stop on an unknown native argument/exit contract, encoding, credential source, remote trust boundary, provider semantics, or desired post-state.

## Output Contract

- PowerShell decision with pipeline and target-state paths error native encoding remoting credentials provider module version first and repeat outcomes evidence limits routes and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [pipeline error and native contracts](references/pipeline-error-and-native-contracts.md) | targeted | Pipeline binding errors native arguments/exits streams or encoding changes | Object error native-process stream and encoding behavior remain unchanged | task-agent, review-agent, analysis-agent | decision-record, residual-risk |
| [remoting provider and administration contracts](references/remoting-provider-and-administration-contracts.md) | targeted | Remoting credentials providers modules policy privilege or idempotent administration changes | No remote secret provider module or target-state boundary changes | task-agent, review-agent, analysis-agent | selected-approach, proof-limit, residual-risk |
