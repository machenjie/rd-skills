---
name: containerization
description: Designs reproducible, minimal, non-root, secret-free container images with separated build and runtime concerns, health behavior, shutdown handling, provenance, and reduced supply-chain risk.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "72"
changeforge_version: 0.1.0
---

# Mission

Package software into container images that are **reproducible, minimal, non-root, secret-free, and content-addressed** — with build and runtime concerns cleanly separated, health and shutdown behavior documented, and supply-chain provenance attached — so that the image behaves identically from CI through production and presents the minimum exploitable attack surface.

# When To Use

Use this capability when creating or modifying: a `Dockerfile` or `Containerfile`, a multi-stage build configuration, a base image selection or upgrade, a container runtime configuration (`docker-compose`, Kubernetes Pod spec, ECS task definition), health check and readiness behavior, image publishing and tagging strategy, build context definition (`.dockerignore`), or container startup and shutdown lifecycle. Also use it when a dependency vulnerability in the runtime image requires layer remediation.

# Do Not Use When

Do not use this capability to design cluster scheduling, service mesh, or ingress routing — use `kubernetes-gateway`. Do not use it for secret rotation or vault integration — use `secret-configuration-security`. Do not use it for CI image-build automation — use `ci-cd`. Do not use it to hide non-deterministic build processes; fix the build process first.

# Non-Negotiable Rules

- **Multi-stage builds.** Build stage has compilers, package managers, test tooling, dev certificates. Runtime stage has **only** what is needed to run and diagnose the app. Copy artifacts explicitly; never `COPY . .` into the runtime stage.
- **Non-root user.** The application process runs as a named non-root user and group (e.g., `USER appuser:appuser`). If the platform genuinely requires root (legacy bind-mount, `/proc` manipulation), document it, restrict via `securityContext`, and escalate to a security review.
- **No secrets in image layers.** No credentials, tokens, private keys, `.env` files, SSH keys, or API keys in any layer — including build-stage layers (they remain in layer history). Inject secrets at runtime via environment variables from a secrets manager, mounted volumes, or the platform's secrets API (Kubernetes Secrets, AWS Secrets Manager, Vault agent injector).
- **Pin base image to digest.** `FROM debian:bookworm-slim@sha256:abc...` not `FROM debian:latest`. Tag-only pins are mutable; an upstream tag change silently produces a different image. Update digests via Dependabot / Renovate automation.
- **Minimal base image.** Prefer distroless (`gcr.io/distroless`), Alpine (`alpine:3.x`), or slim images (`debian-slim`, `python:3.x-slim-bookworm`). Avoid `ubuntu:latest` or full-fat images in runtime stage unless specifically required. Fewer packages = smaller CVE surface.
- **Deterministic dependency installation.** `npm ci --frozen-lockfile`, `pip install --require-hashes -r requirements.txt`, `go mod download` with `go.sum` verification, `mvn dependency:resolve -Dsettings=...`. Never `RUN pip install --upgrade` without version pinning.
- **Build context is minimal.** `.dockerignore` excludes: `.git`, `node_modules`, local caches, test output, `.env*`, IDE configs, generated artifacts not needed in build. Oversized build context slows builds and risks leaking local state.
- **Runtime configuration via environment or mounted config.** No hard-coded database hosts, queue URLs, feature flags, environment names, account ids, or region strings baked into layers. Twelve-Factor App principle VI.
- **Health, readiness, and liveness probes.** Service-facing containers must define a `HEALTHCHECK` (Docker) or readiness/liveness probes (Kubernetes). Health must verify the application can actually serve traffic, not just that the process is alive (`/healthz` returning 200, not `CMD echo ok`).
- **Graceful shutdown.** Container catches `SIGTERM`, drains in-flight requests (within a configured timeout), and exits cleanly. Kubernetes sends `SIGTERM` before `SIGKILL`; apps that don't handle it may drop in-flight requests on scale-down.
- **Image is content-addressed for promotion.** Image referenced by digest in deployment manifests; same digest promoted from dev → staging → production. Mutable tags (`latest`, branch name) are never used in production manifests.
- **SBOM and vulnerability scan.** Generate SBOM at build time (`syft`, `crane sbom`); run vulnerability scan (`Trivy`, `Grype`, `Snyk`) in CI; block on CRITICAL CVEs in runtime OS packages and direct app dependencies.

# Industry Benchmarks

Anchor against: **OCI Image Specification (Open Container Initiative)** for image format and layer standards. **NIST SP 800-190** (Application Container Security Guide) — four risk areas: image, registry, orchestration, container runtime. **OWASP Docker Security Cheat Sheet** — top 12 Docker controls. **CIS Docker Benchmark v1.6** — scored hardening checklist for Docker daemon and images. **CIS Kubernetes Benchmark** (pod spec controls that flow from image design). **SLSA v1.0** — build provenance for SLSA L2 requires a hosted build platform + signed provenance; images should carry provenance attestation (`cosign attest`). **Sigstore / Cosign** for keyless image signing with OIDC. **Syft + Grype (Anchore)** / **Trivy (Aqua Security)** / **Snyk Container** for SBOM and CVE scanning. **Google Distroless** — language-specific base images with no shell, no package manager, minimal OS libs; ideal runtime base. **Chainguard Images** — hardened, daily-rebuilt distroless alternatives. **Docker multi-stage build** documentation and best practices. **Twelve-Factor App** (Factor III — config in environment; Factor VI — stateless process) for runtime configuration discipline. **Buildkit / BuildX** for cache mounts, secret mounts (`--secret`), SSH mounts (`--ssh`) to avoid leaking secrets in layers. **Hadolint** (Dockerfile linter) for enforcing best-practice rules. **Dockle** for CIS benchmark compliance scoring. **Docker Scout** / **AWS Inspector** / **Google Artifact Analysis** for registry-integrated scanning. **Kaniko / ko / Buildah** for rootless/daemonless builds in CI.

### Base Image Selection Matrix

| Base image | OS size | Shell | Package manager | CVE surface | Pick when |
| --- | --- | --- | --- | --- | --- |
| **`gcr.io/distroless/base-nossl`** | ~2 MB | None | None | Minimal | Compiled binaries (Go, Rust, C++); nothing else needed |
| **`gcr.io/distroless/java21`** | ~85 MB | None | None | Low | JVM apps; no shell exploitability |
| **`gcr.io/distroless/python3`** | ~50 MB | None | None | Low | Python apps; no pip at runtime |
| **`alpine:3.x`** | ~5 MB | `ash` | `apk` | Low | Lightweight; shell available if debug tools needed; musl libc edge cases |
| **`debian:bookworm-slim`** | ~75 MB | `bash` | `apt` | Medium | glibc required; familiarity; `apt` for runtime deps |
| **`ubuntu:24.04-minimal`** | ~30 MB | `bash` | `apt` | Medium | Requires Ubuntu userland specifically |
| **`chainguard/*`** | 5–100 MB | None/optional | None | Very low | Hardened distroless with daily updates |
| **Language official slim** (`python:3.x-slim`) | 50–200 MB | `bash` | `apt` | Medium | Prototyping; developer familiarity |
| **Full official** (`python:3.x`, `node:20`) | 300–900 MB | Yes | Yes | High | **Only** build stage; never runtime stage |

### Multi-Stage Build Structure

```dockerfile
# ---- Build stage ----
FROM python:3.12-slim-bookworm AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --require-hashes --no-cache-dir -r requirements.txt --target /install
COPY src/ ./src/

# ---- Runtime stage ----
FROM gcr.io/distroless/python3-debian12:nonroot AS runtime
# Copy only compiled/installed artifacts from build stage
COPY --from=builder /install /usr/lib/python3/dist-packages
COPY --from=builder /build/src /app/src
# Explicit non-root (distroless nonroot = uid 65532)
USER nonroot:nonroot
WORKDIR /app
ENTRYPOINT ["python3", "-m", "myapp"]
```

Key properties: builder has pip (attack surface); runtime has no shell, no pip, no root, no build cache. Secrets used during build injected via `RUN --mount=type=secret` (BuildKit), **never** `ARG`/`ENV`.

### Secret Injection Anti-patterns

| Anti-pattern | Why it fails |
| --- | --- |
| `ENV DB_PASSWORD=secret` in Dockerfile | Password baked into every layer; visible in `docker history` and registry |
| `ARG SECRET_TOKEN` / `RUN curl -H "Token: $SECRET_TOKEN"` | `ARG` value visible in image metadata; also in build cache |
| `COPY .env .` | `.env` in every layer; `.dockerignore` must exclude but is often incomplete |
| `RUN ssh-keygen && echo "$PRIVATE_KEY" > /root/.ssh/id_rsa` | Key in layer history permanently |
| **Correct**: `RUN --mount=type=secret,id=db_pass cat /run/secrets/db_pass` | Secret available only during that RUN step; never in layer |
| **Correct**: Runtime env var from Kubernetes Secret / Vault injector | Secret injected at runtime, not baked into image |

### Health Check Design

| Layer | Implementation | Checks |
| --- | --- | --- |
| **Docker `HEALTHCHECK`** | `HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD ["/usr/bin/grpc_health_probe", "-addr=:8080"]` | Application serves requests |
| **Kubernetes readinessProbe** | `httpGet: path: /readyz port: 8080 initialDelaySeconds: 5` | Dependent services (DB, cache) reachable; app ready to receive |
| **Kubernetes livenessProbe** | `httpGet: path: /livez port: 8080 failureThreshold: 3` | App not deadlocked; auto-restart if stuck |
| **Kubernetes startupProbe** | Longer `failureThreshold`; protects slow-starting apps from premature liveness kill | Initial startup window |

Health endpoint MUST NOT: execute expensive DB queries, require network calls to external services, or be behind authentication. MUST return 200 when ready, 503 when not.

# Selection Rules

Select this capability when **image construction, runtime safety, or container artifact design** is primary. Adjacent routing:

- Prefer `ci-cd` for image build automation, registry publishing, promotion policy, and supply-chain controls (SBOM, signing, scan gates).
- Prefer `kubernetes-gateway` for cluster deployment contracts, Kubernetes resource spec, ingress, and service mesh.
- Prefer `secret-configuration-security` for vault integration, secret rotation, and mounted-secret design.
- Prefer `dependency-vulnerability-scanning` for broad SCA analysis beyond the container image layer.
- Prefer `project-initialization` for initial repository and runtime layout.

# Risk Escalation Rules

Escalate when: the image runs in privileged mode or requires `SYS_ADMIN` / `NET_ADMIN` capabilities, the runtime user is root and cannot be changed without platform work, the base image has CRITICAL CVEs that cannot be patched in the short term, the image processes regulated data (PII/PHI/PCI) and the supply-chain provenance is absent, third-party or vendor-supplied binaries are included without a security review, the image is deployed to multi-tenant infrastructure, a `securityContext.allowPrivilegeEscalation: true` is requested, or the image is a distro-level base shared by multiple services (blast radius = all services).

# Critical Details

Container security is about **minimizing exploitable surface at build time and enforcing runtime constraints**. Key refinements:

- **Layer cache and build reproducibility.** Instruction order determines cache efficiency and reproducibility. Place rarely-changed instructions first (OS packages, system deps), frequently-changed last (app code). Use BuildKit cache mounts (`--mount=type=cache`) to persist package manager caches without baking them into layers.
- **`COPY` specificity.** `COPY . .` copies everything in build context including generated noise, IDE configs, and `.env` files if `.dockerignore` has gaps. Always `COPY src/ /app/src` with explicit paths.
- **`RUN` layer explosion.** Each `RUN` creates a layer. Chaining (`&&`) keeps intermediate state (package cache, temp files) out of layers. Always `apt-get install && apt-get clean && rm -rf /var/lib/apt/lists/*` in the same `RUN`.
- **`USER` before `CMD`/`ENTRYPOINT`.** Setting `USER` early means later `RUN` commands also run as that user during build; be deliberate. For production, set immediately before `CMD` after all setup is done as root.
- **File ownership.** `COPY --chown=appuser:appuser` in runtime stage ensures files are readable by the runtime user. Missing chown causes runtime permission errors.
- **Writable paths.** Container filesystem should be read-only at runtime (`readOnlyRootFilesystem: true` in Kubernetes securityContext); applications needing writable paths use `emptyDir` or explicit volume mounts.
- **`CMD` vs `ENTRYPOINT`.** `ENTRYPOINT ["app"]` is the process; `CMD ["--flag"]` are default args. Use `ENTRYPOINT` in exec form (JSON array, not shell string) to receive signals directly, not via shell. Shell form (`RUN "cmd"` or `ENTRYPOINT "cmd"`) starts a shell that catches SIGTERM and may not forward it.
- **`EXPOSE` is documentation only.** It does not open ports; it does communicate intent to operators and tooling. Use it for the ports the service actually binds.
- **`HEALTHCHECK` vs Kubernetes probes.** In Kubernetes, `HEALTHCHECK` is advisory; Kubernetes readiness/liveness probes are authoritative. Define both. The Kubernetes probes should align with `HEALTHCHECK` intent.
- **Signal handling.** Go / Python / Node / JVM apps must handle `SIGTERM` explicitly. Java JVMs require `exec java ...` (exec form) or a dedicated shutdown hook. Node.js must register `process.on('SIGTERM', ...)`.
- **Init process.** Long-running containers with child processes (e.g., Celery worker spawning sub-workers) need a proper init to reap zombies: `tini` (`docker init`) or Kubernetes `shareProcessNamespace` + explicit zombie reaping.
- **Image provenance attestation.** `cosign attest --predicate build-provenance.json image@sha256:...` generates in-toto provenance attestation stored alongside the image in the registry. Admission controllers (Sigstore Policy Controller, Kyverno, OPA Gatekeeper) can enforce "only images with valid attestation run in this cluster."
- **Vulnerability scan cadence.** Scanning only at build time is insufficient; base image vulnerabilities are disclosed daily. Registry-integrated scanning (Docker Scout, AWS Inspector, GCR On-Push) scans the image continuously and alerts when new CVEs affect already-deployed images.
- **`.dockerignore` hygiene.** A minimal `.dockerignore` that excludes `.git`, `node_modules`, `__pycache__`, `.env*`, `*.log`, `*.test`, IDE directories is non-negotiable. Review it alongside the Dockerfile in code review.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `FROM python:3.12` (full image) in runtime stage | 1 GB+ runtime image; 800 packages; dozens of CVEs; unnecessarily large attack surface |
| `COPY . .` in runtime stage | Copies `.env`, `.git`, local caches, test data, IDE files into production image |
| `ENV DB_PASSWORD=...` | Password baked into image; any `docker inspect` reveals it |
| `CMD ["sh", "-c", "python app.py"]` | Shell captures SIGTERM; Python never receives it; container killed by SIGKILL after timeout → requests dropped |
| No `.dockerignore` | Build context includes `node_modules` (hundreds of MB); slow build; risk of local state leakage |
| `FROM node:20-alpine` tag only (no digest) | Tag re-pointed upstream; image pulled next week is different; silent regression |
| Health check: `CMD echo ok` | Process alive ≠ app serving; health passes during complete application failure |
| Container runs as root with no documented justification | Any RCE = full host root (if docker socket mounted) or full container filesystem |
| Multi-stage: copy entire `/` from builder to runtime | No separation; build tools ship to production |

# Failure Modes

- Runtime image ships compilers, package managers, dev certs, or test tooling → attack surface enlarged; CVE count inflated.
- Container runs as root without documented platform need → any RCE gives attacker root.
- `DB_PASSWORD` as `ENV` in Dockerfile → secret visible in registry image history and `docker inspect`.
- `FROM node:20-alpine` without digest → upstream tag re-pointed → different image ships silently.
- `CMD ["sh", "-c", "app"]` wraps in shell → SIGTERM captured by `sh` → graceful shutdown timeout → requests dropped on scale-down.
- No `HEALTHCHECK` / readiness probe → traffic routed to starting or unhealthy containers.
- `.dockerignore` absent → `.env` file, `.git`, `node_modules` copied into build context → secrets in layers or multi-GB image.
- SBOM not generated → cannot answer "does any deployed image contain libxyz < 1.2.3?" when CVE is disclosed.
- Build not reproducible → staging and production run different images if rebuilt from the same tag.
- Container has read-write root filesystem → exploited container can modify binaries, write malware.
- Init process absent → zombie children accumulate under worker manager → OOM or PID exhaustion.
- Health endpoint authenticates or queries DB expensively → health check kills healthy container under load.
- `COPY --chown` missing → files unreadable by non-root runtime user → crash on startup.
- Port declared in Kubernetes spec not `EXPOSE`d → operators and auto-detection miss it; misconfiguration undetected.

# Output Contract

Return a containerization plan with:

- `image_purpose` (service type, runtime class)
- `base_image_selection` (full digest-pinned reference; justification; CVE surface assessment)
- `build_stages` (stage name, from image, purpose, artifacts produced, secrets injected via mount not baked)
- `runtime_contents` (what is and is not present; justified)
- `user_and_permissions` (uid:gid; filesystem ownership; read-only rootfs; writable paths via volume)
- `configuration_sources` (environment, mounted config, platform secrets — nothing baked)
- `secret_exclusions` (mechanism preventing secrets in layers; BuildKit secret mounts; `.dockerignore` contents)
- `exposed_ports` (port, protocol, purpose)
- `signal_handling` (SIGTERM handler; exec vs shell form; init process if needed)
- `health_behavior` (healthcheck command; readiness/liveness/startup probes in Kubernetes form; what the endpoint checks)
- `sbom` (tool, format CycloneDX/SPDX, attachment point)
- `vulnerability_scan` (tool, threshold for blocking, registry-integrated scan policy)
- `image_signing` (cosign/sigstore; provenance attestation; admission policy reference)
- `artifact_tags` (digest-pinned reference; immutable tag policy; mutable convenience tags)
- `build_reproducibility` (lockfile enforcement; cache mount strategy; BuildKit version pinning)
- `dockerignore_contents` (explicit list of excluded patterns)
- `verification_checks` (post-build checks: user, port, layer count, SBOM, scan, provenance)

# Quality Gate

The containerization plan passes only when:

1. Multi-stage build separates build tools from runtime; runtime stage contains only what is needed.
2. Base image is pinned to digest; updated via automation (Renovate/Dependabot).
3. Application runs as named non-root user; file ownership matches.
4. No secrets, credentials, or tokens present in any layer (verified by secret-scan and `docker history` review).
5. All dependencies installed via lockfile with hash verification; no `latest` or floating versions.
6. `.dockerignore` excludes `.git`, `.env*`, caches, test output, IDE files.
7. Runtime configuration injected at runtime; nothing environment-specific baked.
8. Health check or readiness probe verifies application serves traffic; not just process alive.
9. `CMD`/`ENTRYPOINT` uses exec form; SIGTERM reaches the application process.
10. SBOM generated; vulnerability scan run; CRITICAL runtime CVEs resolved or risk-accepted with owner.
11. Image content-addressed by digest in deployment manifests; mutable tag not used in production.
12. Build is reproducible: same git SHA → same digest (or documented reason why not).

# Used By

- delivery-release-gate

# Handoff

Hand off to `ci-cd` for image build automation, publishing, SBOM attachment, signing, and scan gates; `dependency-vulnerability-scanning` for SCA analysis; `secret-configuration-security` for vault integration and mounted-secret design; `kubernetes-gateway` for cluster deployment, pod spec security context, and ingress; `delivery-release-gate` for artifact promotion readiness.

# Completion Criteria

The capability is complete when the container image is **minimal, digest-pinned, multi-stage, secret-free, non-root, signal-aware, health-verified, SBOM-attached, scanned, and content-addressed in deployment manifests** — indistinguishable by artifact between dev, staging, and production, and presenting the smallest exploitable attack surface for its runtime purpose.
