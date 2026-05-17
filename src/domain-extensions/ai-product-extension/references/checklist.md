# AI Product Extension Checklist

- Model output is labeled and handled as uncertain unless independently verified.
- RAG retrieval applies the same permission, tenancy, retention, and redaction rules as the source system.
- Embedding creation, indexing, deletion, and refresh behavior are defined.
- Prompt and context assembly separates system rules, user input, retrieved data, tool results, and generated output.
- Prompt injection and indirect injection scenarios are reviewed.
- Tool calls have least privilege, typed arguments, side-effect classification, confirmation rules, and audit logs.
- Evaluation data covers happy path, edge cases, refusals, hallucination-prone prompts, adversarial prompts, and regressions.
- Failure behavior covers model timeout, rate limit, tool failure, empty retrieval, low confidence, and unsafe output.
- Observability includes quality metrics, retrieval hit quality, tool-call outcomes, refusal rates, latency, cost, and drift.
- User-facing claims cite evidence or explain uncertainty when the product depends on factual accuracy.
