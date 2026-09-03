# Trust-Sensitive Filesystem And Process Protection

- Apply protection only to a current filesystem or direct child-process effect with concrete reachable trust evidence, or to one complete related `critical_unknown`.

**Load when:** A current filesystem or direct child-process effect has concrete reachable trust evidence, or a complete related Core critical unknown remains.

**Do not load when:** Only normal filesystem or process correctness applies, or trust evidence is generic, disconnected from the current effect, or unreachable.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `proof-limit`, `residual-risk`

## One Decision

Start from `same_trust_principal` without treating it as safety proof. Load this decision only through concrete-evidence or complete-related-`critical_unknown`; generic possibility remains a Proof Limit.

## Material Assessment

Evaluate these three dimensions independently before deciding whether their current relationship is material.

### Less-trusted actor, input, or writer

- Identify the current actor, input, or writer and the exact filesystem or process effect it can influence. Ordinary mutability, path difference, or future replacement is not this evidence.

### Privilege or sensitive asset

- Identify the privilege, secret, credential, protected object, or sensitive consumer that changes the consequence. Capability alone does not grant authorization.

### Reachable material impact path

- Trace the current effect from the less-trusted influence to the privileged or sensitive consequence. A disconnected possibility does not satisfy `material_assessment`.

Material escalation requires all three dimensions. Their absence does not prove that no security risk exists, and independent concurrency, retry, durability, recovery, privacy, supply-chain, and integration risks remain active.

## Protection Decisions

| Concrete current evidence | Protection decision | Failure signal |
|---|---|---|
| Less-trusted writer controls an attacker-controlled path, link, or reparse point | Bind traversal and mutation to a trusted opened base and object identity | A check/open race redirects the current effect |
| ACL or security descriptor affects a sensitive object | Apply and verify the effective protection at creation or replacement | Bytes or authority become accessible beyond the intended principal |
| Less-trusted writer feeds a privileged consumer | Separate writable inputs from the privileged consumption boundary | Privileged behavior consumes substituted content |
| Untrusted executable lookup can select the child | Bind program identity and allowed lookup directories before invocation | Search order selects a less-trusted program |
| Credential or sandbox authority changes child access | Minimize and bind credentials, environment authority, working directory, and sandbox policy | The child receives unintended authority |
| Secret handle exposure can cross process inheritance | Allowlist inherited handles and verify closure on every terminal path | A child retains a secret-bearing handle or token |

## Failure Rules

- Stop editing when a complete related `critical_unknown` lacks a required actor, fact, plausible impact path, or material consequence.
- Do not manufacture a hostile writer from a same-principal local resource, generic unknown, ordinary path difference, or possible future replacement.
- Preserve normal correctness and every independent risk even when this Reference does not load.

## Primary Sources

- [Microsoft `CreateFileW`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
- [Microsoft reparse points and file operations](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points-and-file-operations)
- [Microsoft file security and access rights](https://learn.microsoft.com/en-us/windows/win32/fileio/file-security-and-access-rights)

## Proof Limits

Static source and vendor contracts do not establish live writer identity, effective ACLs, link or reparse behavior, privilege, handle inheritance, or sandbox enforcement. Record the unresolved current fact and its residual owner.
