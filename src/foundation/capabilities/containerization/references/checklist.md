# Containerization Checklist

- Separate build dependencies from runtime dependencies.
- Use a controlled base image and dependency version policy.
- Exclude credentials, caches, local files, and source control metadata from the build context.
- Run as non-root when feasible and validate file permissions.
- Keep runtime configuration out of image layers.
- Define ports, health behavior, shutdown behavior, and writable paths.
- Scan image and dependencies where release policy requires it.
- Verify the produced image matches the expected artifact and tag policy.
