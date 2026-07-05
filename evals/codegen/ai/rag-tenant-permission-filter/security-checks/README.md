# Security Checks

## Threat Surface

This benchmark touches RAG permission filtering, tenant isolation, retrieval provenance, LLM context safety. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that permission filters are part of the retriever contract, not post answer cleanup.
- Verify that provenance records include document id, tenant id, and permission decision.
- Verify that vector search and metadata filtering semantics are covered by integration tests.
- Verify that prompt construction treats retrieved text as untrusted context.

## Rejection Cases

- Reject any solution that uses filtering unauthorized chunks only after the LLM answer is generated.
- Reject any solution that uses relying on prompt instructions to hide restricted documents.
- Reject any solution that uses using tenant filters without object level permission checks.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
