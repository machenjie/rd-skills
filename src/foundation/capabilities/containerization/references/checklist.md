# Containerization Checklist

- Map every Dockerfile/Containerfile, build context, entrypoint, compose/orchestrator reference, CI image build, registry tag, and deploy manifest image reference in scope.
- Separate build dependencies from runtime dependencies; copy only explicit artifacts into the runtime stage.
- Use a digest-pinned base image and dependency version policy; record rejected base alternatives and CVE/compatibility tradeoffs.
- Exclude credentials, caches, local files, test output, and source control metadata from the build context through `.dockerignore` and secret scanning.
- Run as a named non-root user, validate file ownership, read-only rootfs behavior, and writable volume paths.
- Keep runtime configuration out of image layers; use platform config and managed secret sources.
- Verify ports, health/readiness/liveness behavior, startup semantics, shutdown/SIGTERM handling, and init needs.
- Generate SBOM, run image and dependency vulnerability scans, and record exceptions with owner and expiry.
- Attach or verify signing/provenance when release policy requires it; prove deploy manifests reference the expected digest.
- Close with graph/memory/execution judgment, artifact-to-runtime validation map, validation commands/output/exit codes, rollback-to-prior-digest path, residual risks, and next gate.
