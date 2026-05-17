# Example Output

```markdown
## Role Inventory

| Actor | Type | Goal | Authority | Risk |
| --- | --- | --- | --- | --- |
| Finance analyst | Human role | Run monthly export | Read accounts in assigned tenant | May infer closed account history |
| Support agent | Privileged support role | Diagnose export issue | Read export metadata only | Must not download tenant data without approval |
| Export worker | Service account | Generate file asynchronously | Read eligible account records | Needs least-privilege storage write access |
| Accounting platform | External system | Import CSV | Consume stable file contract | Breaks if columns change |

Downstream models:
- Permission matrix for analyst, support agent, and worker.
- Contract test for accounting platform.
```
