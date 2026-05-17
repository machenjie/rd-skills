# Example Output

```markdown
## Runtime Decision

Workload: IO-bound API service with strict API contracts.
Selected: TypeScript on Node.js with strict mode and schema validation.
Rejected: Python, because existing team ownership and SDK type generation favor TypeScript.
Runtime Risks: Event-loop blocking and package supply chain.
Required References: language-idiom-enforcement, language-testing-strategy, typescript-professional-usage.
Decision: Accept with runtime validation and bundle/dependency review.
```
