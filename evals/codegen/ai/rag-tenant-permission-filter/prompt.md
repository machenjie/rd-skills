# Benchmark Prompt

## Task

Implement a focused change to enforce tenant and object permission filters in a RAG retrieval path before model context assembly.

## Context

The starter repo represents an assistant retrieves documents from a vector index and passes snippets to an LLM answer step. In its initial state, the starter behavior filters by similarity score but not by tenant or object level permission. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Retrieval only returns chunks the actor can read at query time.
- Tenant and object filters are applied before prompt context assembly.
- Denied chunks are excluded from citations and model input.
- Tests prove cross tenant and revoked access snippets cannot leak.

## Constraints

- Permission filters are part of the retriever contract, not post answer cleanup.
- Provenance records include document id, tenant id, and permission decision.
- Vector search and metadata filtering semantics are covered by integration tests.
- Preserve the existing public contract unless the prompt explicitly asks for a compatible addition.
- Do not replace the benchmark with documentation-only output.

## Deliverables

- Source changes in the starter repo that implement the requested behavior.
- Tests or executable checks that prove the required behavior and denial paths.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
