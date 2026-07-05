# Package Ecosystem Command Map

Use this reference to choose concrete dependency evidence commands for the inspected ecosystem. Prefer repository-native scripts when they already wrap these commands with the same flags and lockfile policy.

# Command Map

| Ecosystem | Frozen install / resolution | Graph evidence | Vulnerability evidence | License / SBOM evidence |
| --- | --- | --- | --- | --- |
| npm | `npm ci` | `npm ls --all` | `npm audit --omit=dev` or `osv-scanner` | `npm sbom` or CycloneDX npm plugin |
| pnpm | `pnpm install --frozen-lockfile` | `pnpm list --depth Infinity` / `pnpm why <pkg>` | `pnpm audit` or `osv-scanner` | CycloneDX pnpm plugin / syft |
| Yarn Berry | `yarn install --immutable` | `yarn why <pkg>` / constraints report | `yarn npm audit` or `osv-scanner` | CycloneDX yarn plugin / syft |
| pip | `pip install --require-hashes -r requirements.txt` | `pipdeptree` | `pip-audit` | CycloneDX Python plugin / syft |
| uv | `uv sync --frozen` | `uv tree` | `pip-audit` or `osv-scanner` against exported lock data | CycloneDX Python plugin / syft |
| Poetry | `poetry install --no-update` | `poetry show --tree` | `poetry export` + `pip-audit` / `osv-scanner` | CycloneDX Python plugin / syft |
| Go | `go mod download` / `go build` with `go.sum` | `go mod graph` / `go mod why <module>` | `govulncheck ./...` | `syft` / CycloneDX Go module tooling |
| Rust | `cargo build --locked` | `cargo tree` / `cargo tree -f "{p} {f}"` | `cargo audit` | `cargo cyclonedx` / syft |
| Maven | `mvn -B verify` with lock/plugin policy | `mvn dependency:tree -Dverbose` | OWASP Dependency-Check / `osv-scanner` | CycloneDX Maven plugin |
| Gradle | `gradle --write-verification-metadata` plus dependency locking | `gradle dependencies` / `dependencyInsight` | OWASP Dependency-Check / `osv-scanner` | CycloneDX Gradle plugin |
| Ruby | `bundle install --deployment` | `bundle viz` / `bundle info` / `bundle why` where available | `bundle audit` | CycloneDX Ruby plugin / syft |
| PHP | `composer install --no-dev --prefer-dist` | `composer show --tree` | `composer audit` | CycloneDX PHP plugin / syft |
| Elixir | `mix deps.get --only prod` with `mix.lock` | `mix deps.tree` | `mix hex.audit` / `osv-scanner` | syft or ecosystem SBOM plugin |
| Containers | `docker pull <image>@sha256:<digest>` | image layer/package inventory | Trivy / Grype | syft / Trivy SBOM |

# Selection Notes

- Use the repository's pinned package-manager and runtime versions before trusting command output.
- Prefer frozen or locked resolution commands for validation; plain update/install commands are evidence of mutation, not reproducibility.
- Capture command, working directory, package-manager version, exit code, log/report path, and whether network access was used.
- For monorepos, run both root graph checks and isolated package install/build checks for independently published or deployed packages.
- For generated SDK/client packages, include the source spec/schema, generation command, generated diff, and drift check in the dependency evidence.
- For native extensions or container images, validate the deploy target OS/libc/CPU/image digest, not only the local developer platform.
- If a command is unavailable in the repository, record the missing tool as an evidence limit and route to the relevant gate instead of substituting unrelated output.
