# Containerization Benchmarks And Patterns

Use this reference when `containerization` needs more depth than the main `SKILL.md` should carry efficiently. Keep the main body focused on routing, evidence, output, and gates; use this file for base-image matrices, build/runtime separation patterns, supply-chain evidence, graph/memory/execution coupling, validation patterns, and anti-pattern review.

## Benchmark Anchors

- OCI Image Specification and Docker/BuildKit multi-stage builds for image format, layers, build context, cache, and secret-mount behavior.
- NIST SP 800-190, OWASP Docker Security Cheat Sheet, and CIS Docker/Kubernetes benchmarks for container runtime hardening.
- SLSA, in-toto, Sigstore/Cosign, registry scanning, and SBOM practice for provenance and artifact trust.
- Distroless, Chainguard, Alpine, Debian slim, and language slim images for base-image tradeoffs.
- Hadolint, Dockle, Trivy, Grype, Snyk, Syft, Docker Scout, and registry-integrated scanners for lint, SBOM, and vulnerability evidence.
- Twelve-Factor runtime config and immutable artifact promotion for environment separation.

## Base Image Selection Matrix

| Base image | Runtime fit | Avoid when | Evidence required |
| --- | --- | --- | --- |
| Distroless / Chainguard | Compiled binary or JVM/Python runtime with no shell/package manager needed. | Debug shell, package manager, or native runtime tools are required in production. | Digest, runtime smoke, file/user inspection, scan summary. |
| Alpine | Small image with shell and `apk`; useful for lightweight services. | glibc-only native dependencies, musl incompatibility, or opaque vendor binaries. | Native dependency test, scan summary, ABI risk note. |
| Debian/Ubuntu slim | glibc required, predictable OS packages, shell needed for diagnostics. | Runtime can be distroless or package manager is left installed unnecessarily. | Package list, cleanup proof, CVE exception owner. |
| Language official slim | Early service or language runtime convenience with bounded size. | Full image or package manager remains in runtime without justification. | Lockfile install, runtime contents inspection, migration plan to smaller base when needed. |
| Full official language image | Builder stage only. | Runtime stage. | Explicit build-stage purpose and artifact copy list. |

## Build And Runtime Separation

| Area | Strong pattern | Weak pattern to reject |
| --- | --- | --- |
| Build context | `.dockerignore` excludes `.git`, `.env*`, caches, local outputs, and unused test artifacts. | `COPY . .` with no context review. |
| Secret use | BuildKit `--mount=type=secret` or runtime platform secret source. | `ARG TOKEN`, `ENV PASSWORD`, copied `.npmrc`, SSH key, or secret in layer history. |
| Dependency install | Lockfile and hash enforcement; no floating upgrade at build time. | `pip install --upgrade`, `apt-get upgrade`, or package install without version policy. |
| Runtime stage | Explicit artifact copy, non-root user, owned files, no compiler/package manager unless justified. | Copying the whole builder filesystem into runtime. |
| Process model | Exec-form entrypoint, signal handler, optional init for child processes. | Shell-form command that swallows SIGTERM. |
| Health behavior | Health/readiness checks prove application can serve expected traffic. | `echo ok` or process-only check. |

## Graph, Memory, And Execution Coupling

Treat repository graph, project memory, and execution trajectory as discovery inputs until current files and validation prove them.

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Dockerfile, Containerfile, `.dockerignore`, entrypoint, compose/K8s/ECS refs, CI image build, and deploy image digest are inspected. | Only the edited Dockerfile is inspected while deploy refs still point to a mutable tag. |
| Project memory | Prior base image, digest policy, runtime user, secret-injection pattern, or health contract still matches current source and platform policy. | Memory predates a base-image upgrade, registry move, CI change, or runtime platform split. |
| Execution trajectory | Build, lint, inspect, run, scan, SBOM, and provenance evidence ran after the final image-related edit. | Validation predates Dockerfile, lockfile, `.dockerignore`, or deploy-reference changes. |
| Release evidence | Prior digest, promotion path, and rollback image are named and verified. | Rollback depends on a mutable tag or a rebuilt image rather than the prior digest. |

## Validation Evidence Patterns

- Build proof: clean-context image build command, exit code, resulting digest, and build logs without secrets.
- Runtime contents proof: image inspection, package/file list, runtime user, file ownership, exposed port, and read-only/writable path checks.
- Secret proof: `.dockerignore` review, secret scan, layer history inspection, and no credential-bearing build args in output.
- Health/shutdown proof: container start, health/readiness hit, SIGTERM stop, drain timeout, and init/zombie behavior when workers fork.
- Supply-chain proof: SBOM artifact, vulnerability scan report, exception owner, signature/provenance record, and registry/admission evidence if available.
- Promotion proof: deploy manifest uses digest, same digest moves across environments, and rollback points to prior digest.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Runtime `FROM python:3.12` full image. | Large attack surface and unnecessary CVEs. | Builder uses full image; runtime uses slim/distroless with explicit artifacts. |
| `COPY . .` in runtime stage. | Secrets, local state, test data, and caches ship. | Explicit copy list plus `.dockerignore`. |
| `ENV DB_PASSWORD=...`. | Secret persists in image history and registry. | Runtime secret source or BuildKit secret mount. |
| Tag-only base or production image. | Silent upstream retag or wrong artifact promotion. | Digest-pinned base and deploy refs. |
| Shell-form entrypoint. | SIGTERM not forwarded; scale-down drops traffic. | Exec-form entrypoint and signal handler. |
| No SBOM or scan. | CVE response cannot identify affected deployed images. | Generate SBOM and scan runtime image in CI/registry. |
| Health check only tests process existence. | Unready app receives traffic. | Probe validates service readiness cheaply and safely. |

## Handoff Boundaries

- Use `ci-cd` when image build automation, registry publishing, signing, SBOM attachment, and scan gates are primary.
- Use `dependency-vulnerability-scanning` when SCA policy, CVE triage, accepted exceptions, or license/provenance review dominates.
- Use `secret-configuration-security` when secret rotation, vault integration, secret mount policy, or key custody is primary.
- Use `kubernetes-gateway` when pod securityContext, probes, ingress, service, or cluster admission policy is primary.
- Use `delivery-release-gate` when artifact promotion, rollback, deployment watch, or regulated release evidence is primary.
