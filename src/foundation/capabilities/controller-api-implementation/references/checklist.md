# Controller API Implementation Checklist

- Identify route, method, operation owner, and API contract.
- Parse transport inputs without embedding business decisions.
- Invoke trusted validation and map validation failures to stable errors.
- Extract authentication context and pass it to the use case or policy layer.
- Confirm object-level authorization is invoked before protected operations.
- Delegate workflow, transactions, persistence, and domain decisions outside the controller.
- Map service results to response body, status code, and headers.
- Convert known errors to client-safe responses and hide raw internals.
- Include correlation or request context in diagnostics.
- Add controller or contract tests for success, validation, auth, and error paths.
