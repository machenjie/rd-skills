# Starter Repo

## Stack

Minimal Python and Markdown fixture repository prepared by the shared codegen benchmark harness.

## Initial State

This starter repo models a tiny delivery workflow. Update the implementation and provide bounded compaction evidence.

## Files

- `compaction_workflow.py` contains the tiny implementation under test.
- `tests/` contains repository-local validation tests.
- `COMPACTION_CONTEXT.json` and `CAPABILITY_EVIDENCE.md` may be created by the candidate as bounded evidence.

## Constraints

- Do not introduce personal corpus ingestion, external archive mappings, or hidden runtime state.
- Do not store raw prompts, secrets, full command output, local absolute user paths, full diff body, or full file contents.
- Keep fixture changes small and tied to the benchmark prompt.

Validation command:

```bash
python3 -m unittest discover -s tests
```
