# Backend Checklist

- Validate all trusted-boundary inputs.
- Enforce authn, authz, ownership, tenancy, and role checks.
- Define transaction scope and isolation expectations.
- Make commands idempotent where retries are possible.
- Handle concurrency and duplicate requests.
- Define retry, timeout, and async job behavior.
- Use consistent error codes and response shape.
- Add structured logs, metrics, and traces where useful.
- Cover unit, integration, regression, and failure tests.
