# Logging design scenario

Review a webhook handler logging change. The hot path records the complete request body, including email, bearer token, and signature. Every intermediate retry exception is emitted at error level. The ingress request, queue message, and handler have no shared correlation value. One detailed event is emitted for every item in a high-volume batch. Permission-change audit events use the same diagnostic payload, sink, access policy, and retention. Define the acceptable logging contract and the evidence required before release.
