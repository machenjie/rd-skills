# Starter Repo

## Stack

A minimal Python and Markdown fixture repository prepared by the shared codegen benchmark harness.

## Initial State

The starter repository contains small text and Python files that are safe to edit during live benchmark runs. The fixture is intentionally bounded so the agent must produce evidence for Caller Callee Test Impact Map without relying on external services or hidden state.

## Files

- `CAPABILITY_EVIDENCE.md` may be created or updated to hold assertion-backed process evidence.
- `src/` files may be updated only when the case needs concrete code behavior.
- `tests/` files may be added by the candidate when validation is part of the task.

## Constraints

- Do not introduce personal corpus ingestion, external archive mappings, or runtime-specific archives.
- Do not store raw prompts, secrets, full command output, or local absolute user paths.
- Keep fixture changes small and tied to the benchmark prompt.
- Preserve existing harness entrypoints and repository-local validation commands.
