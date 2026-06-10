Selected stage: code-review.
Selected professional skill: backend-change-builder.
Selected capabilities: java-jvm-professional-usage.

Hidden risks: Java executor without shutdown or bounds; thread pool lifecycle leak; interruption behavior not handled.

Inspected boundaries: executor owner, queue size, shutdown path, request timeout, interruption behavior, blocking task, and JVM heap/thread saturation risk.

Evidence required: executor ownership and shutdown evidence; queue bound and timeout evidence; interruption behavior validation.

Output obligations covered: thread executor lifecycle evidence; validation evidence for shutdown or timeout; what evidence proves and does not prove; residual JVM runtime risk owner.

Validation command: `./gradlew test --tests ExecutorLifecycleTest` (not run in fixture; expected outcome is shutdown, timeout, and interruption assertions).
What evidence proves: the inspected executor has bounded lifecycle and handles interruption for covered paths.
What evidence does not prove: production heap pressure, all thread interleavings, or downstream latency.

Residual risk: production saturation needs load evidence; owner: reliability-observability-gate.
Next gate: quality-test-gate before merge.
