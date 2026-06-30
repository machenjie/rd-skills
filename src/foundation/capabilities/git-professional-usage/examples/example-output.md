# Example Output

## Input Scenario

A merge conflict touches `api/user.proto`, generated TypeScript client files, and a handwritten service. The user asks to "just take ours" so the branch can be pushed.

## Selected Capability

`git-professional-usage`

## Decision Record

- Operation: merge conflict resolution.
- State inspected: current branch, upstream, `git status --short`, conflicted paths, ours/theirs for the proto and service files.
- Generated artifact policy: `api/user.proto` is authoritative; generated TypeScript clients are derived and must be regenerated.
- Decision: resolve the proto by preserving the new optional field and the existing field number; regenerate clients; manually inspect the handwritten service for compatibility.
- Rejected shortcut: wholesale `ours` would drop the upstream field and break deployed clients.

## Evidence Checklist

- Worktree state recorded before resolution.
- Both sides of each conflict inspected.
- Generated output regenerated rather than hand-edited.
- Same-pattern scan performed for the field name and generated client import.
- Unrelated user changes left unstaged.

## Validation Commands

```
git status --short
git diff -- api/user.proto src/services/user.ts
npm run generate:proto
npm test -- user-service
```

## Residual Risk

Downstream consumers outside the repository were not tested. Owner: API maintainer. Follow-up trigger: consumer contract failure or generated SDK publish.

## Handoff Summary

Resolved merge conflict by preserving source contract and regenerating derived clients. No destructive Git operation was used. Remaining risk is external consumer compatibility.
