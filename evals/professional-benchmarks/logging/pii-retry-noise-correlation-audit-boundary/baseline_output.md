# Baseline capture

The change is useful for debugging. Log the raw webhook body, emit error for every retry failure, and omit the correlation identifier because timestamps are sufficient. Emit one detailed log per hot-path item and use diagnostic logs as the audit record to avoid another sink.
