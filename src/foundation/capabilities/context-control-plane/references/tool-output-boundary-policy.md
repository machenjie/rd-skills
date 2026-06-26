# Tool Output Boundary Policy

Tool output entering route context must be small, relevant, and privacy-safe.
Hook runtime state stores boundary records, not raw tool output.

## Keep

- command or tool name
- exit status or outcome
- relevant excerpt or parsed summary
- artifact path or report path
- affected files, validators, or cases
- negative evidence and residual risk
- output size class, line/byte counts, digest, and LLM context policy

## Exclude

- raw prompts
- secrets, credentials, tokens, and environment values
- full command output when a parsed outcome is enough
- full diffs or full file contents
- hook-captured raw stdout or stderr
- production personal data
- personal archives and private mapping artifacts

If output is truncated or the runtime exposes no output metadata, record what
was retained, what was omitted, whether the runtime is degraded, and whether the
omission limits validation evidence. Do not mark closure as passed from a
runtime that cannot expose the needed output facts.

## Hook Boundary Record

When hook telemetry observes a tool result, retain only:

- `tool_name` and `event_name`
- `output_size_class` (`none`, `small`, `large`, `unknown`, or `unsupported`)
- `output_bytes` and `output_lines` when provided or safely inferred
- `artifact_path` only when it is repo-relative or cache-scoped after
  sanitization
- `digest` of observed output facts or runtime-provided digest
- `bounded_summary`
- `truncation_advice`
- `llm_context_policy` (`inline_bounded`, `artifact_reference_only`,
  `rerun_with_redirect`, or `unsupported_runtime`)
- `privacy_status`
- `unsupported_reason`

Never persist raw `stdout`, `stderr`, `command_output`, `full_diff`,
`file_contents`, `raw_prompt`, environment values, secrets, credentials, or
tokens in this record.

Full artifacts are explicit user/tool artifacts. If full evidence is needed,
rerun with redirection or create a slice/report artifact, then reference the
path and validation status in the final handoff.
