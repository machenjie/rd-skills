# Build Tool Professional Usage Checklist

- Identify the authoritative build surface: tool, target/task, package/module, config file, CI target, and release artifact when relevant.
- Declare graph boundaries: inputs, outputs, direct dependencies, generated sources, toolchain, platform, environment variables, lockfiles, and package boundaries.
- Record generated artifact authority: source spec, generator version/config, output path, committed/ignored policy, and drift command.
- Compare local, CI, and release commands when a local build result is used as evidence.
- Review cache behavior: local/remote cache mode, action-key inputs, generated inputs, lockfiles, tool versions, platform, and nondeterministic time/path/env reads.
- Review task selection: affected targets, transitive consumers, generated-output consumers, and full-suite or cache-bypass fallback when graph confidence is weak.
- Classify validation commands as read-only analysis, generated-output write, cache write, artifact write, package download, release publish, or source/HOME/global-cache mutation.
- Record artifact reproducibility when output ships: command, path, checksum or digest, source ref, dependency lock, toolchain, provenance/signing status, and rebuild limit.
- Validate with the smallest command or artifact that can fail for the changed build boundary, then state what it proves and does not prove.
- Treat repository graph, project memory, old CI logs, and prior artifacts as selectors only until current source/config/build evidence confirms them.
