Selected stage: testing.
Selected professional skill: quality-test-gate.
Selected capabilities: regression-testing, agent-execution-discipline.

Hidden risks: test passes before fix and is not a real regression test; defect recurrence path not protected; completion claim without red-before-fix evidence.

Inspected boundaries: BUG-4812 defect report, coupon total calculation test file, pre-fix commit, fixed branch, CI regression gate, and adjacent currency fixture boundary.

Evidence required: pre-fix failing command output; post-fix passing command output; defect reference linked to test.

Output obligations covered: red-before-fix evidence; green-after-fix evidence; what evidence proves and does not prove; residual risk owner.

Validation command: `python3 -m pytest tests/test_coupon_rounding.py::test_bug_4812_coupon_total_rounds_half_up` (not run in fixture; expected outcome is pre-fix failure output followed by post-fix pass output).
What evidence proves: the exact BUG-4812 recurrence path is blocked by a test that fails on the unfixed code and passes after the fix.
What evidence does not prove: adjacent currencies, concurrent coupon application, production-only decimal configuration, or untested clients.

Residual risk: adjacent currency rounding variants remain untested; owner: quality-test-gate.
Next gate: code-review after red/green command output is attached.
