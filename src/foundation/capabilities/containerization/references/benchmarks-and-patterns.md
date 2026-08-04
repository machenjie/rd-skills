# Containerization Selection Patterns

Load this reference when base, build isolation, runtime content, process, or provenance mechanisms compete and the root rules do not select one.

## Selection Axes

| Surface | Decision question | Evidence |
| --- | --- | --- |
| Base/runtime | Which ABI, certificates, timezone data, native libraries, diagnostics, or compliance controls are actually required? | Runtime dependency inventory, smoke tests, package/file inspection, and update owner. |
| Build isolation | Which compilers, package managers, credentials, and generated assets can be excluded from the final image? | Build/runtime artifact map, copied-file allowlist, layer/history inspection, and clean build. |
| Context and copy | Which local, generated, secret-like, or irrelevant files can enter the builder or cache? | Context rule, ignore policy, same-pattern scan, and produced-image inspection. |
| Process | How do PID 1, signals, child processes, drain, timeout, and exit status interact with the application? | Start/stop test, handler behavior, child reaping, and failure outcome. |
| Runtime authority | Which user, capability, device, namespace, and writable path does the process need? | Declared identity, ownership, read/write test, exception owner, and platform boundary. |
| Artifact identity | How are mutable base/dependency inputs resolved and how does the deploy reference identify the result? | Input policy, source revision, image digest, registry path, deploy reference, and rollback artifact. |

## Failure Patterns

- Reducing size without runtime inspection can remove required trust stores or diagnostics while retaining privileged or secret-bearing content.
- A multi-stage build still leaks when copied artifacts, metadata, caches, or logs contain sensitive material.
- A non-root declaration still fails when ownership, writable paths, bind mounts, or runtime platform identity differ.
- A passing startup probe misses signal forwarding, drain, child reaping, or readiness failure during rollout.
- A digest in one report is irrelevant when CI, registry, deploy, and rollback records name different artifacts.

## Ownership Boundaries

- `ci-cd` owns hosted build, publish, and promotion policy; `kubernetes-gateway` owns pod, service, and routing controls.
- `dependency-vulnerability-scanning` owns package/CVE exceptions; `delivery-release-gate` owns rollout and recovery authority.
