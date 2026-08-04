---
name: containerization
description: "`task-agent`/`review-agent`: use when image layers, build context, runtime user, secrets, health checks, shutdown, or provenance change; skip when container behavior is unaffected."
---

# containerization

## Registry Trigger

**Use when**

- container image change affects build context, layer contents, runtime user and group, filesystem, process or health and shutdown behavior, or artifact provenance

**Do not use when**

- image definition and container runtime contract are unchanged

## Skill Role

Define the image build-to-runtime contract, retained content, runtime authority, process lifecycle, artifact identity, and proof limits. Exclude hosted promotion and cluster routing.

## High-Value Rules

- Connect build definition, context, base and dependency inputs, produced image, registry identity, and deploy reference so validation and rollback name the same artifact.
- Choose build/runtime isolation from the reviewed runtime artifacts, libraries, certificates, diagnostics, and generated assets.
- Keep secret material out of retained layers, metadata, cache exports, logs, and copied config. Select ephemeral build access or runtime injection from the build and platform trust boundary.
- Derive runtime user, group, capabilities, ownership, and writable paths from application behavior.
- Record why elevated authority or a writable root filesystem is needed and who accepts it.
- Define PID 1, signal forwarding, child reaping where the process can spawn children, drain, termination timeout, and exit codes. The platform health contract distinguishes the intended failure state for each selected startup, readiness, liveness, or shutdown signal.
- Govern mutable base tags, package indexes, downloads, and toolchains through current provenance and update policy; prove ABI/runtime compatibility after base or runtime-content changes.
- Validate the resulting image, not only the build file: inspect contents and history, run as the declared user, exercise writable paths, health and termination, scan the artifact, and state proof limits.

## Anti-Patterns

- A small image can still contain a secret, incompatible libc, unsafe entrypoint, excessive privilege, or untraceable artifact.
- Dockerfile review does not prove the final context, cache, generated content, registry digest, or deploy reference.
- A process-only health check or signal-swallowing wrapper can turn rollout or scale-down into traffic loss and restart loops.

## Stop Conditions

- Escalate privileged or root execution without bounded need, suspected secret retention, unknown image lineage, unowned base-risk exception, or termination behavior that can lose or duplicate in-flight work contrary to the workload contract.
- Stop image approval when the artifact cannot be tied to inspected inputs and the intended deploy reference.

## Output Contract

- Return a container decision: define build/runtime boundary, artifact identity, privilege, filesystem, process, probes, validation, rollback, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | base build isolation runtime contents process or provenance choices compete | existing image and runtime policy resolve the changed boundary | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | image change affects context contents identity filesystem probes shutdown or rollback | no container build or runtime boundary changes | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | digest content user secret health shutdown scan or rollback claims need fresh proof | no image artifact-to-runtime claim awaits validation | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
