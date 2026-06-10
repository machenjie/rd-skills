Selected stage: code-review.
Selected professional skill: delivery-release-gate.
Selected capabilities: shell-cli-professional-usage.

Hidden risks: shell unquoted variable can delete wrong path; secret exposed through process list; destructive script lacks dry-run and trap cleanup.

Inspected boundaries: `TARGET` validation, quoted rm path, glob behavior, dry-run/apply switch, trap cleanup, secret passing method, stdout/stderr contract, and shellcheck lane.

Evidence required: quoted path and target validation evidence; secret handling boundary; shellcheck and dry-run validation.

Output obligations covered: shell execution safety evidence; validation evidence for shellcheck or dry-run; what evidence proves and does not prove; residual CLI safety risk owner.

Validation command: `shellcheck cleanup.sh && bats tests/cleanup.bats` (not run in fixture; expected outcome is target-validation, dry-run, and failure cleanup evidence).
What evidence proves: the inspected destructive path is quoted, guarded, dry-run capable, and avoids process-list secret exposure.
What evidence does not prove: every OS distribution, production filesystem state, or external command behavior.

Residual risk: operator runbook still needs release review; owner: delivery-release-gate.
Next gate: security-privacy-gate for secret-handling approval.
