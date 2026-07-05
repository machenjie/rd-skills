# Example Output

## AI Domain Findings
- Blocking: retrieved documents must be filtered by user permission before prompt assembly and again before citation display.
- Required evaluation: at least one fixture set for correct answer, no-answer, stale answer, prompt injection, cross-tenant leakage, and tool failure.
- Tool policy: the agent may draft changes automatically but must require explicit confirmation before sending, deleting, purchasing, or publishing.

## Verification
- Offline eval with pass thresholds for groundedness, refusal correctness, retrieval precision, and unsafe-action prevention.
- Integration tests for permission-filtered retrieval and low-confidence fallback.
- Production monitoring for hallucination reports, empty retrieval, tool errors, latency, and cost.
