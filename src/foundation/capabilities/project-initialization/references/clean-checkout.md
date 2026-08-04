# Clean Checkout Evidence

Load this reference when initialization closure depends on proving that bootstrap, build, or tests do not rely on ambient workstation state.

## Evidence Record

- Identify source revision, supported platform or container, toolchain file, package manager, lockfiles, workspace roots, and generated-artifact starting state.
- Run the documented bootstrap path in a fresh clone or declared clean environment with command, exit status, produced files, external services, and network or credential requirements recorded.
- Run the task-relevant build, test, lint, format-check, generated-drift, dependency, secret, and documentation checks after the final scaffold change.
- Verify required config fails clearly when absent and examples contain non-secret placeholders.
- Name cache, global tool, home-directory, platform, private-registry, provider, and production assumptions that the clean environment did not exercise.
- Record artifact or concise result paths, not full logs or raw sensitive output.

## Closure Rules

- Mark proposed but unexecuted commands as not run.
- Re-run affected proof after changing toolchains, lockfiles, bootstrap scripts, generated policy, example config, source-of-truth commands, or setup documentation.
- Treat local clean-checkout success as repository bootstrap evidence, not production deployability, cloud permission, provider availability, organization-wide compliance, or future developer-platform parity.
