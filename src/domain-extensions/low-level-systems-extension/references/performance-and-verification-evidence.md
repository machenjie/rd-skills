# Performance And Verification Evidence Pattern

Use this evidence-pattern Reference only for the named low-level performance-and-verification evidence decision.

## Decision Rules

- Tie optimization to a representative workload, baseline, variance, resource budget, and regression decision; preserve correctness, ABI, and tail behavior while changing structure.
- Select sanitizer, fuzz, race, stress, boundary, fault-injection, platform-matrix, and leak evidence from reachable undefined behavior, concurrency, parser, ABI, and resource risks.
- Absence claims bind diagnostics to a supported compiler/target/build matrix and stated state space. Unproved inputs, schedules, platforms, and foreign-code behavior remain residual risk.
- Observe actionable crashes, panics, assertions, latency, throughput, memory, descriptor or handle pressure, retries, and recovery outcomes without exposing unsafe memory or secrets.
