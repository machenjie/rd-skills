# Error Code Design Industry Benchmarks

Load this reference only when reviewing public API error semantics, SDK compatibility, or release documentation.

## Benchmark Anchors

Anchor against: **RFC 7807** (Problem Details for HTTP APIs, 2016) and **RFC 9457** (updated 2023) - canonical standard for HTTP error response format: `type` (URI), `title` (human-readable type summary), `status` (HTTP status code), `detail` (human-readable explanation of this specific occurrence), `instance` (URI that identifies this specific occurrence). Media type: `application/problem+json`. **RFC 9110** (HTTP Semantics, 2022) - authoritative source for HTTP status code definitions; 4xx = client errors (do not retry same request); 5xx = server errors (may retry). **gRPC Status Codes** (google.rpc.Code) - 16 canonical codes: `OK`, `CANCELLED`, `UNKNOWN`, `INVALID_ARGUMENT`, `DEADLINE_EXCEEDED`, `NOT_FOUND`, `ALREADY_EXISTS`, `PERMISSION_DENIED`, `UNAUTHENTICATED`, `RESOURCE_EXHAUSTED`, `FAILED_PRECONDITION`, `ABORTED`, `OUT_OF_RANGE`, `UNIMPLEMENTED`, `INTERNAL`, `UNAVAILABLE`; use `google.rpc.ErrorInfo`, `BadRequest`, `QuotaFailure` detail types. **OWASP Error Handling Cheat Sheet** - log complete error details server-side; return minimal safe detail to clients; never expose stack traces; use generic messages for unexpected errors. **OWASP API8:2023** - Security Misconfiguration; do not expose debug information or implementation details. **CWE-209** - Information Exposure Through an Error Message - classified as a CWE/SANS Top 25 weakness. **W3C TraceContext** (Trace-Context, 2021) - `traceparent` and `tracestate` HTTP headers for distributed trace propagation; mandatory for microservice error correlation. **Zalando RESTful API Guidelines** - error responses must be `application/problem+json`; use `violations` array for field-level validation errors; error `type` must be documented. **Google AIP-193** (Errors) - gRPC and REST error handling; `status.details` for machine-readable error context; `BadRequest.FieldViolation` for field-level errors. **Stripe Error Model** - widely cited industry benchmark for API error design: `error.type`, `error.code`, `error.message`, `error.param`; consistent retryability signals. **Twilio / GitHub API errors** - consistent HTTP status mapping with structured machine-readable codes.

## HTTP Status Code Decision Matrix

| Situation | Correct status | Wrong status (common mistake) |
| --- | --- | --- |
| Request body missing required field | `400 Bad Request` | `422 Unprocessable Entity` (reserved for semantic errors in valid syntax) |
| Request body syntactically invalid (malformed JSON) | `400 Bad Request` | `500 Internal Server Error` |
| Semantic validation failure (field value violates business constraint) | `422 Unprocessable Entity` | `400` (syntax is valid; meaning is wrong) |
| Authentication token missing or not parseable | `401 Unauthorized` | `403 Forbidden` |
| Valid token but insufficient permissions | `403 Forbidden` | `401` |
| Authenticated, no permission, existence sensitive | `404 Not Found` | `403 Forbidden` (leaks existence) |
| Resource not found (safe to reveal existence) | `404 Not Found` | `200` with error in body |
| Business rule violation (e.g., insufficient balance) | `422 Unprocessable Entity` or `409 Conflict` | `400 Bad Request` |
| Idempotent request replayed (already done) | `200 OK` (return result) or `204 No Content` | `409 Conflict` |
| Conflicting concurrent modification | `409 Conflict` | `500 Internal Server Error` |
| Rate limit exceeded | `429 Too Many Requests` + `Retry-After` header | `503 Service Unavailable` |
| Transient server failure (retry safe) | `503 Service Unavailable` + `Retry-After` | `500 Internal Server Error` |
| Permanent server error (non-retryable) | `500 Internal Server Error` | `503` |
| Downstream dependency unavailable | `502 Bad Gateway` or `503` | `500` |
| Request canceled by client | `499` (nginx convention) / close connection | N/A |

## RFC 7807 / 9457 Error Response Schema

```json
{
  "type": "https://api.example.com/errors/INSUFFICIENT_FUNDS",
  "title": "Insufficient Funds",
  "status": 422,
  "detail": "The account has a balance of $12.50, but the transaction amount is $50.00.",
  "instance": "/transactions/txn_abc123",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "requestId": "req_01HXQY3N2E",
  "extensions": {
    "availableBalance": "12.50",
    "requestedAmount": "50.00",
    "currency": "USD"
  }
}

// Field-level validation error (RFC 9457 extension):
{
  "type": "https://api.example.com/errors/VALIDATION_ERROR",
  "title": "Validation Error",
  "status": 400,
  "detail": "One or more fields failed validation.",
  "instance": "/users",
  "traceId": "...",
  "violations": [
    {
      "field": "email",
      "message": "Must be a valid email address.",
      "rejectedValue": "not-an-email"
    },
    {
      "field": "age",
      "message": "Must be at least 18.",
      "rejectedValue": 15
    }
  ]
}
```

## Error Code Taxonomy Table

| Error code | HTTP status | gRPC code | Category | Retryable? | User action | Idempotency |
| --- | --- | --- | --- | --- | --- | --- |
| `VALIDATION_ERROR` | 400 | `INVALID_ARGUMENT` | Input | No | Fix input fields | N/A |
| `AUTHENTICATION_REQUIRED` | 401 | `UNAUTHENTICATED` | Auth | Maybe (re-auth) | Log in again | N/A |
| `PERMISSION_DENIED` | 403 | `PERMISSION_DENIED` | Auth | No | Contact admin | N/A |
| `NOT_FOUND` | 404 | `NOT_FOUND` | Resource | No | Check resource ID | N/A |
| `CONFLICT` | 409 | `ABORTED` | State | No (resolve conflict) | Review current state | N/A |
| `PRECONDITION_FAILED` | 412 | `FAILED_PRECONDITION` | State | No (fetch ETag first) | Fetch latest version | If-Match |
| `UNPROCESSABLE_REQUEST` | 422 | `INVALID_ARGUMENT` | Business | No | See detail | N/A |
| `RATE_LIMITED` | 429 | `RESOURCE_EXHAUSTED` | Capacity | Yes (after Retry-After) | Wait and retry | Yes |
| `INTERNAL_ERROR` | 500 | `INTERNAL` | Server | No (human review) | Contact support | No |
| `UPSTREAM_UNAVAILABLE` | 503 | `UNAVAILABLE` | Server | Yes (exponential backoff) | Retry automatically | Idempotent only |
| `GATEWAY_ERROR` | 502 | `UNAVAILABLE` | Server | Yes (after delay) | Retry automatically | Idempotent only |
| `REQUEST_TIMEOUT` | 408/504 | `DEADLINE_EXCEEDED` | Server | Yes (idempotent only) | Retry if idempotent | Must check |

## Retryability Decision Tree

```
Error received from API
├── 4xx (Client Error)?
│   ├── 400, 401, 403, 404, 409, 410, 422 → NOT RETRYABLE
│   │   (same request will produce same error; fix input or re-authenticate)
│   └── 429 (Rate Limited) → RETRY after Retry-After header value
│       └── No Retry-After? → Exponential backoff: 1s, 2s, 4s, 8s, cap 60s
└── 5xx (Server Error)?
    ├── 500 → NOT RETRYABLE (permanent server fault; human investigation needed)
    ├── 502, 503, 504 → RETRYABLE
    │   ├── Is the original request IDEMPOTENT?
    │   │   ├── YES (GET, PUT, DELETE, or uses Idempotency-Key) → RETRY safely
    │   │   └── NO (POST without Idempotency-Key) → CHECK SIDE EFFECT FIRST
    │   │       → Query state before retrying a non-idempotent request
    │   └── Backoff: 1s × 2^attempt + jitter, max 3–5 retries, cap 60s
    └── Connection error / timeout
        └── Same as 502/503/504 → treat as transient; apply idempotency check
```
