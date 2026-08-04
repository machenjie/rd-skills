# Containerization Checklist

- Map the changed build definition, context, base and dependency inputs, entrypoint, produced image, registry identity, deploy reference, and rollback artifact.
- Separate build-only capability from required runtime content; account for copied artifacts, native libraries, certificates, diagnostics, generated assets, and provenance.
- Check retained layers, metadata, cache exports, logs, and copied config for secret material; identify the approved ephemeral build or runtime injection path.
- Derive user, group, capability, device, namespace, ownership, writable-path, root-filesystem, and bounded-exception policy with an accountable owner from actual runtime behavior.
- Define the container-side process and health contract for PID 1, signals, child processes where present, drain, termination, exit codes, and each health state consumed by the target platform.
- Resolve mutable bases, package indexes, downloads, and toolchains under current update and provenance policy; verify ABI and runtime compatibility after relevant changes.
- Produce vulnerability, SBOM, signing, or provenance evidence when changed risk or release policy requires it, and tie that evidence to the image digest it describes.
- Validate each changed claim against the built image with applicable inspection, smoke, writable-path, health, termination, scan, artifact-to-deploy, proof-limit, and rollback-artifact evidence.
