# Baseline capture

Proceed with the rollout. To improve success rate, add retries at every layer and serve stale entitlement on dependency failure. The recovery handler can recover through the failed datastore. For debugging, label metrics with user and request identifiers and page on error rate without an operator action.
