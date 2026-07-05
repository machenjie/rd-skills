# Security Checks

## Threat Surface

Publishing events or cache state before commit can expose or act on uncommitted data.

## Required Checks

- Reject event publication before commit.
- Fail if cache is updated from uncommitted state.
- Reject duplicate event publication on retries.

## Rejection Cases

- Reject completion without commit-failure tests.
- Reject generic helper placement that hides transaction ownership.

