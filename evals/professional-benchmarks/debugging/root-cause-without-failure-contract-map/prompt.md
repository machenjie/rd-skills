Diagnose an intermittent payment retry bug. The notes reproduce duplicate
charges and identify a timeout, but they do not map the symptom or root cause
to a violated idempotency invariant, retry boundary, side effect, or failure
contract before proposing a patch.

