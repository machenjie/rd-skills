# Package Ecosystem Command Map

Use this reference to select dependency evidence commands. Prefer repository scripts only when they preserve the same fail-closed contract.

The versions below match official stable releases checked on 2026-07-16. A repository pin overrides this baseline and requires version-specific verification.

## Frozen Command Map

| Ecosystem / verified version | Committed precondition | Fail-closed resolution or install | Source-write status | Graph evidence | Vulnerability evidence | License or SBOM evidence |
| --- | --- | --- | --- | --- | --- | --- |
| npm 12.0.1 | Manifests, `package-lock.json` or shrinkwrap, and graph-affecting `.npmrc` | `npm ci` | Replaces `node_modules`; the command contract keeps manifests and lock unchanged | `npm ls --all` | `npm audit` | `npm sbom` |
| pnpm 11.13.1 | Manifests, workspace config, and `pnpm-lock.yaml` | `pnpm install --frozen-lockfile` | Frozen mode rejects lockfile updates; store and `node_modules` may change, while source proof still rejects manifest, workspace-config, or lockfile diffs | `pnpm list --depth Infinity`; `pnpm why <pkg>` | `pnpm audit` | CycloneDX pnpm plugin or syft |
| Yarn 4.14.1 | Manifests, `yarn.lock`, `.yarnrc.yml`, pin, and tracked install artifacts | `yarn install --immutable`; add `--immutable-cache --check-cache` for Zero-Installs | Lock and immutable paths stay unchanged; install artifacts may change | `yarn why <pkg>` | `yarn npm audit` | CycloneDX Yarn plugin or syft |
| pip 26.1.2 | Fully pinned, hash-complete requirements, generator drift check, and fresh virtual environment | `python -m pip install --require-hashes --no-deps -r requirements.txt` | Requirements stay unchanged; environment and cache change | `python -m pip inspect`; `python -m pip check` | `pip-audit` | `cyclonedx-py` or syft |
| uv 0.11.29 | `pyproject.toml`, workspace metadata, and `uv.lock` | `uv lock --check`; then `uv sync --locked` | Lock stays unchanged; `.venv` and cache change | `uv tree --locked` | `pip-audit` against locked export | CycloneDX export or syft |
| Poetry 2.4.1 | `pyproject.toml`, project config, and `poetry.lock` | `poetry check --lock`; then `poetry sync` | Valid lock stays unchanged; environment and cache change | `poetry show --tree` | Export plugin plus `pip-audit` | CycloneDX Python tool or syft |
| Go 1.26.5 | `go.mod`, `go.sum`, optional workspace files, and toolchain pin | `go mod tidy -diff`; then `go build -mod=readonly ./...` and matching tests | Tidy check is non-writing; expected build writes are module cache and outputs | `go mod graph`; `go mod why -m <module>` | `govulncheck ./...` | CycloneDX Go tool or syft |
| Rust 1.97.0 | Workspace manifests, `Cargo.lock`, Cargo config, and toolchain pin | `cargo fetch --locked`; then workspace build and tests with `--locked` | Lock stays unchanged; Cargo home and `target/` change | `cargo tree --locked --workspace` | `cargo audit` | `cargo cyclonedx` or syft |
| Maven 3.9.16 | Pinned POM, BOM, plugins, wrapper, toolchain, Enforcer, checksum-fail policy, and project verifier | No core frozen command; after cache prefill, run the project verifier and `mvn -B -C -o -nsu verify` | Core cannot prove a lock; `.m2` and `target/` may change | Offline `dependency:tree` under the same policy | OWASP Dependency-Check or OSV-Scanner | CycloneDX Maven plugin |
| Gradle 9.6.1 | Wrapper, strict locks for the relevant configuration set, disabled changing modules, and `verification-metadata.xml` | Repository task resolving the declared configuration set with `--dependency-verification=strict` | Frozen invocation excludes lock-writing and verification-writing flags; caches and build outputs may change | Per-project `dependencies` and `dependencyInsight` | OWASP Dependency-Check or OSV-Scanner | CycloneDX Gradle plugin |
| Bundler 4.0.16 | `Gemfile`, `Gemfile.lock`, config, and an isolated bundle path when exact cleanup matters | `BUNDLE_FROZEN=true bundle install`; use `BUNDLE_DEPLOYMENT=true` only for deployment path semantics | Environment form writes no config or lock; gem path and cache change | `bundle list`; `bundle info <gem>` | `bundle audit` | `cyclonedx-ruby` or syft |
| Composer 2.10.2 | `composer.json`, committed `composer.lock`, PHP platform, and config | Assert lock existence; run `composer validate --strict --check-lock`; then `composer install --no-interaction` | Lock stays unchanged; `vendor/`, cache, scripts, and plugins may write | `composer show --locked --tree` | `composer audit` | CycloneDX Composer plugin or syft |
| Mix 1.20.2 | `mix.exs`, root or shared `mix.lock`, Elixir, OTP, Hex, and Rebar pins | `MIX_ENV=prod mix deps.get --only prod --check-locked` | Lock stays unchanged; `deps/` and `_build/` change | `MIX_ENV=prod mix deps.tree` | `mix hex.audit` | Ecosystem SBOM tool or syft |
| Docker Engine 29.6.1 | Full registry/repository digest and selected platform | `docker image pull --platform=<os/arch> <registry>/<repo>@sha256:<digest>` | Expected mutation is the daemon image store; source postcondition rejects repository changes | `docker buildx imagetools inspect <ref>@sha256:<digest>` | `docker scout cves` | `docker scout sbom` |

## Verification Contract

- Match the exact repository-pinned manager and runtime before using a row.
- Verify committed preconditions through source-control evidence.
- Run frozen proof in a clean or disposable checkout.
- Reject diffs to manifests, locks, workspace metadata, package-manager config, and verification metadata.
- Classify cache, environment, build-output, and daemon-store changes separately from source mutation.
- Treat lifecycle scripts, plugins, and build hooks as possible source writers.
- Match dependency groups, extras, workspaces, and target platforms to the locked selection.
- Use full-graph `npm audit` for general dependency-risk evidence. Scope `--omit=dev` to a production-runtime artifact and separately scan build/test/CI dependencies or record the unverified gap for `dependency-vulnerability-scanning`.
- Keep update, repair, and metadata-write flags out of frozen proof.
- Record command, working directory, version, exit code, report path, and network mode.
- Record unavailable commands as proof limits for the owning gate.
