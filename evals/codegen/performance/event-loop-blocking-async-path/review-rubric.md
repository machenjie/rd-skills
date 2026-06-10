# Review Rubric

## Passing Standard

The solution passes when the async path no longer blocks the event loop and
fan-out is bounded with cancellation, timeout, and backpressure.

## Scoring

- 30 percent async blocking detection and CPU-bound offload.
- 25 percent blocking versus non-blocking IO boundary.
- 20 percent cancellation, timeout, and backpressure design.
- 15 percent event-loop lag, profile, or stress evidence.
- 10 percent structure placement of worker and IO boundaries.

## Automatic Failure Conditions

- Blocking call on event loop remains.
- CPU-bound work on event loop remains.
- Promise.all or gather unbounded remains.
- No timeout or cancellation.
- No event-loop lag, profile, or overload evidence is requested.

## Reviewer Notes

Strong answers treat async structure as runtime design, not syntax conversion.
The worker boundary should have lifecycle and pool sizing.
