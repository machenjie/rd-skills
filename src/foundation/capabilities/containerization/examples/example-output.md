# Example Output

```markdown
## Container Plan

Image purpose:
- Runtime image for the public API service.

Build separation:
- Builder stage installs dependencies and produces compiled assets.
- Runtime stage contains compiled assets, production dependencies, and process entry only.

Runtime safety:
- Runs as app user.
- No package manager cache or credential files in runtime layers.
- Configuration comes from environment and platform-managed secrets.

Verification:
- Build image from a clean context.
- Run vulnerability scan.
- Start container and verify readiness endpoint, shutdown, and file permissions.
```
