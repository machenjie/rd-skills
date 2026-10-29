# RAG Quality and Retrieval Design

**Reference type:** targeted
**Load when:** Model-backed retrieval needs evidence selection, context assembly, or answer-quality decisions.
**Do not load when:** The task is ordinary search without a model decision or changes no retrieval or answer-quality mechanism.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** decision-record, validation-plan, proof-limit

## Diagnose by Stage

- Bind a query to its expected evidence and answer requirements before changing embeddings, ranking, prompts, or context size.
- Trace corpus, parsing, chunking, retrieval, reranking, context assembly, and answer generation separately.
- Check whether the source contained the evidence before diagnosing retrieval. Missing or malformed parsed content cannot be fixed by reranking.
- Inspect evidence recall before answer quality. A fluent answer can conceal an absent supporting passage.
- Inspect context assembly after retrieval. Deduplication, truncation, ordering, and formatting can discard or distort correctly retrieved evidence.
- Distinguish groundedness from completeness. A supported answer can still omit a required part of the task.
- Check each consequential claim against its cited passage. A real source identifier does not prove that its contents support the claim.

## Select Retrieval Mechanisms

- Compare keyword, vector, and hybrid retrieval on representative queries. Exact identifiers and semantic paraphrases can favor different mechanisms.
- Match chunk boundaries to evidence units, such as sections, table headers, code symbols, and nearby definitions.
- Evaluate chunk size and overlap against recall, duplication, reranking cost, and context consumption together.
- Evaluate embedding, reranker, and context-budget changes against a fixed query set and relevant slices.
- Define behavior for absent, conflicting, or outdated evidence from the product's answer contract. Unsupported certainty is a failure outcome.
- Reuse established source permissions, revocation, freshness, and lineage controls across retrieval and fallback paths.

## Distinguishing Cases

| Case | Diagnosis and evidence |
| --- | --- |
| Correct evidence exists but retrieval misses it | Compare parsed content, chunk membership, candidate recall, and reranker selection |
| Evidence is retrieved but omitted or misread | Inspect assembled context and claim-to-passage interpretation |
| Corpus has no supported answer | Observe the specified abstention, clarification, or limited-answer behavior |
| Sources conflict or have different validity dates | Preserve the conflict and temporal authority instead of selecting by fluency |
| Evidence spans a table, code block, or another language | Verify preserved structure and cross-boundary retrieval |
| Ordinary full-text search changes | Keep the model-specific quality method unloaded |

Return stage-local failures, mechanism comparisons, answer evidence, and uncovered query populations.
Static cases validate these distinctions; model quality requires actual trials on the selected system.

## Evaluation Source

- Compare [retrieval relevance, groundedness, and completeness](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators) without treating one evaluator score as the entire product outcome.
