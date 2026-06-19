# Executor Adapter Evaluation

This generated report uses deterministic local fixtures. It is structural evidence only; live pass-rate, token overhead, and turn overhead remain `not_collected` unless separately measured.

## Summary

- Status: `pass`
- Cases: 20
- Passed: 20
- Failed: 0
- Live pass-rate: `not_collected`
- Token overhead: `not_collected`
- Turn overhead: `not_collected`
- Telemetry sample: `generated`

## Coverage

- Runtimes: claude=5, cline=2, codex=6, copilot=4, openhands=2, roo=1
- Coverage targets: closure_verdict, command_risk, degradation, event_recognition, path_normalization, permission_decision, privacy_redaction, tool_category, validation_freshness_after_edits, validation_outcome
- Pressure cases: absolute_user_path, claude_post_tool_failure, codex_destructive_permission_request, copilot_unsupported_pre_tool, edit_after_validation, failed_validation, full_command_output_field, large_path_list_cap, ready_after_rereview, ready_closure, repair_without_rereview, required_unsupported_check_degraded_ready, review_finding_without_repair, secret_like_payload_field, targeted_test_reported_as_full, unknown_event, unsupported_runtime_event, validation_pass_then_file_changed

## Cases

| Case | Runtime | Status | Event | Gate | Closure | Privacy Redactions |
| --- | --- | --- | --- | --- | --- | --- |
| claude-edit-after-validation | claude | `pass` | `file_changed` | `pass` | `needs_validation` | none |
| claude-failed-validation | claude | `pass` | `post_tool_use` | `pass` | `blocked` | command:kind_only |
| claude-post-tool-failure | claude | `pass` | `post_tool_use_failure` | `pass` | `needs_validation` | command:kind_only |
| claude-ready-after-rereview | claude | `pass` | `stop` | `pass` | `ready` | none |
| claude-validation-pass-then-filechanged | claude | `pass` | `file_changed` | `pass` | `needs_validation` | none |
| cline-plan-mode-edit-degradation | cline | `pass` | `user_prompt_submit` | `degraded` | `needs_validation` | none |
| cline-unknown-event | cline | `pass` | `unknown` | `degraded` | `needs_validation` | none |
| codex-destructive-permission-request | codex | `pass` | `permission_request` | `pass` | `blocked` | command:kind_only |
| codex-full-command-output-redaction | codex | `pass` | `post_tool_use` | `pass` | `needs_validation` | command_output:ignored, stdout:ignored, command:kind_only |
| codex-large-path-list-cap | codex | `pass` | `post_tool_use` | `pass` | `needs_validation` | none |
| codex-ready-edit-validation | codex | `pass` | `stop` | `pass` | `ready` | none |
| codex-secret-like-payload-redaction | codex | `pass` | `user_prompt_submit` | `pass` | `needs_validation` | prompt_text:ignored |
| codex-targeted-test-reported-as-full | codex | `pass` | `stop` | `pass` | `needs_validation` | none |
| copilot-degraded-ready-required-unsupported | copilot | `pass` | `stop` | `pass` | `degraded_ready` | none |
| copilot-repair-without-rereview | copilot | `pass` | `stop` | `pass` | `needs_review` | none |
| copilot-review-finding-without-repair | copilot | `pass` | `stop` | `pass` | `needs_repair` | none |
| copilot-unsupported-pre-tool | copilot | `pass` | `pre_tool_use` | `degraded` | `needs_validation` | command:kind_only |
| openhands-absolute-path-normalization | openhands | `pass` | `file_changed` | `pass` | `needs_validation` | none |
| openhands-test-command-pass | openhands | `pass` | `post_tool_use` | `pass` | `needs_validation` | command:kind_only |
| roo-unsupported-runtime-event | roo | `pass` | `post_tool_use` | `degraded` | `needs_validation` | none |
