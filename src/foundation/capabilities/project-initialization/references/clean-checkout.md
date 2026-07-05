# Clean Checkout Evidence

Use this reference when a project initialization plan needs exact first-checkout proof rather than general scaffold guidance.

## Required Evidence

- Repository state: branch or commit, package manager, toolchain file, OS/container assumptions, and whether generated artifacts were present before setup.
- Setup command: one command or ordered commands an engineer can run from a fresh clone.
- Validation commands: build, lint, format check, tests, secret scan, dependency audit, generated drift check, and docs link check when relevant.
- Environment placeholders: `.env.example` or equivalent with non-secret placeholders and startup validation for required variables.
- Proof limits: what local setup does not prove, such as production deployability, cloud permissions, provider credentials, or organization-wide compliance.

## Clean Checkout Ledger

```yaml
clean_checkout_evidence:
  workspace_source: fresh clone | temporary copy | existing checkout
  toolchain:
    runtime_versions: []
    package_manager: ""
    lockfiles: []
  setup:
    command: ""
    exit_code: null
    duration_or_onboarding_target: ""
  validation:
    - command: ""
      exit_code: null
      artifact_or_log: ""
      proves: ""
      does_not_prove: ""
  environment:
    placeholder_files: []
    startup_config_validation: ""
    secret_scan: ""
  residual_risk:
    owner: ""
    reason: ""
```

## Closure Rules

- Use `not run` rather than `pass` when the command is proposed but not executed.
- Name artifact or result paths instead of pasting full command output.
- Re-run setup-relevant validation after changing lockfiles, toolchain files, bootstrap scripts, generated policy, `.env.example`, CI config, or README setup commands.
