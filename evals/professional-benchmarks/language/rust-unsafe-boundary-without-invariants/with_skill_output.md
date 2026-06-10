Selected stage: code-review.
Selected professional skill: ai-code-review-refactor.
Selected capabilities: rust-professional-usage.

Hidden risks: Rust unsafe boundary without invariants; unsafe block lacks safety contract; FFI ownership can cause use-after-free.

Inspected boundaries: raw pointer provenance, buffer length, ownership transfer, lifetime and aliasing invariants, panic boundary, safe wrapper, and Miri/FFI tests.

Evidence required: unsafe invariant documentation; FFI ownership and lifetime validation; Miri or unsafe-boundary test evidence.

Output obligations covered: unsafe boundary evidence; validation evidence for FFI ownership; what evidence proves and does not prove; residual memory safety risk owner.

Validation command: `cargo test && cargo miri test` (not run in fixture; expected outcome is safe-wrapper and FFI ownership test output).
What evidence proves: the documented unsafe invariants are exercised for the inspected FFI path.
What evidence does not prove: every C caller, all platform ABIs, or all aliasing scenarios.

Residual risk: downstream plugin callers need ABI contract review; owner: architecture-impact-reviewer.
Next gate: low-level-systems-extension review before release.
