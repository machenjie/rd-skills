---
name: project-initialization
description: Defines project structure, configuration, tests, docs, scripts, and deployment surfaces without inventing folders disconnected from architecture.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "71"
changeforge_version: 0.1.0
---

# Mission

**Initialize a repository so that its source layout, test boundaries, configuration surfaces, documentation, build scripts, and deployment assets reflect real architectural responsibilities** — ensuring that every folder has a justified purpose, every engineer can run the verification suite on first checkout, configuration is never stored in source files, and the initial structure does not need to be dismantled in the first feature sprint.

# When To Use

Use this capability when: starting a new repository, service, package, library, or major subsystem from scratch; extracting a new service from a monolith (the new repo needs its own conventions); initializing or restructuring a monorepo/workspace; initializing a new shared library or SDK that will be published internally or publicly; establishing engineering conventions before feature work begins; or when an existing project is being reset (after structural drift, security findings about checked-in credentials, or CI/CD pipeline rebuild).

# Do Not Use When

Do not use this capability to: create folders or scaffolding without a clear architectural justification for each directory (folders must map to runtime boundaries, deployment units, test categories, or documentation responsibilities); initialize a single file or small configuration change in an existing project; make structural decisions that should be deferred to `module-boundary-design` (internal package boundary design within a repository) or `ci-cd` (pipeline-specific automation logic); or install `src/` directories as runtime content when a build step is required to produce distributable artifacts.

# Stage Fit

- **Discovery / intake** — define repository purpose, owner, runtime/deploy target, data classification, and existing conventions before scaffolding.
- **Design / architecture** — map folders to architectural responsibilities, module graph, generated artifacts, and verification boundaries before files are created.
- **Implementation / bootstrap** — require clean-checkout setup, placeholder-only configuration, dependency policy, and runnable validation commands.
- **Review / release readiness** — verify setup evidence, secret scanning, generated artifact policy, docs, ownership, and unresolved handoff gates.

# Non-Negotiable Rules

- **Every top-level folder must have a documented architectural purpose.** A folder named `utils/` with no ownership or boundary definition is a maintenance trap. Acceptable top-level folders: `src/` (source code), `tests/` or `test/` (test suite, mirroring `src/`), `docs/` (operational documentation, architecture decisions, runbooks), `scripts/` (developer and CI automation), `dist/` or `build/` (generated artifacts — gitignored), `config/` (environment-specific configuration templates), `.github/` or `.ci/` (pipeline definitions). Every additional folder must have an OWNERS file or README stating its purpose and boundary.
- **Secrets must never appear in source files, example configurations, `.env.example` files, or committed test fixtures.** `.env.example` must contain placeholder values only (e.g., `DATABASE_URL=postgresql://user:password@host:5432/dbname` — the literal string "password", not a real password). Production secrets must be injected via environment variables or a secrets manager (Vault, AWS Secrets Manager, Azure Key Vault) at runtime — never committed to the repository. Run `git-secrets`, `detect-secrets`, or `truffleHog` as a pre-commit hook and CI gate from day one.
- **Build, test, lint, format, and validate commands must be runnable from a clean checkout in one step.** `make dev-setup` or `npm install && npm test` or `./scripts/bootstrap.sh` — any engineer who clones the repository must be able to reproduce the full verification suite without oral knowledge. Document exact commands in `README.md`. `make` or `Taskfile.yml` are acceptable runners; language-ecosystem conventions (`npm scripts`, `pyproject.toml [tool.poe]`, `Cargo.toml`) are preferred where they exist.
- **Generated artifacts must be separated from authored source and gitignored.** `dist/`, `build/`, `__pycache__/`, `*.egg-info/`, `.next/`, `node_modules/` must be in `.gitignore`. Committing generated artifacts creates merge conflicts, inflates repository size, and creates false diffs in code review. The build system must regenerate them from source reproducibly.
- **Test layout must mirror source layout.** `src/orders/service.py` → `tests/orders/test_service.py`. `src/api/handlers/users.ts` → `tests/api/handlers/users.test.ts`. This convention makes it immediately clear which tests cover which source module and prevents orphaned tests or untested source modules from hiding in unrelated directories.
- **Configuration must use environment variables for all environment-specific values.** Following the Twelve-Factor App (https://12factor.net/config), no environment-specific values (database URLs, API keys, feature flag overrides, logging levels) should be hardcoded in source code or configuration files committed to the repository. Use a `.env.example` file to document required environment variables with descriptions and placeholder values. Provide a validation script that fails fast at startup if required environment variables are missing.
- **Dependency policy must be established before feature work begins.** Define: approved dependency licenses (MIT, Apache-2.0, BSD — copyleft GPL requires legal review); dependency pinning strategy (exact pins in lockfile for applications, range constraints for libraries); automated vulnerability scanning (Dependabot, `npm audit`, `pip-audit`, Snyk) enabled from day one; process for reviewing new dependencies.
- **Monorepos require module graph and build policy on day one.** Before adding packages, define workspace manager, module boundary rules, affected-test selection, incremental build strategy, build cache correctness, generated-file policy, and reproducible local environment.
- **Current graph and memory must constrain scaffolding.** Existing repository conventions, organization standards, prior decisions, and command history are inputs; stale templates or personal preferences are not proof.

# Industry Benchmarks

- **Twelve-Factor App** for config, build/release/run separation, and dev/prod parity.
- **Semantic Versioning** for library/package versioning and public compatibility expectations.
- **OWASP secure coding / supply-chain guidance** for no committed credentials, startup config validation, dependency scanning, SBOM, and artifact signing.
- **Language ecosystem conventions** for source/test layout; prefer accepted ecosystem shape over invented folder taxonomy.
- **ADR, CODEOWNERS, CI template, Make/Taskfile, and reproducible environment conventions** for decision trace, ownership, first-checkout setup, and verification commands.

# Repository Structure Decision Matrix

| Project Type | Source Root | Test Layout | Config Pattern | Build Output | Secrets Management |
| --- | --- | --- | --- | --- | --- |
| Node.js API | `src/` | `tests/` or `src/__tests__/` | `.env` + `dotenv`; validate at startup | `dist/` (gitignored) | env vars; Vault / AWS SSM |
| Python service | `src/packagename/` | `tests/` (mirrors `src/`) | `pydantic-settings` / `python-dotenv`; fail fast on missing | `dist/` / `*.egg-info/` (gitignored) | env vars; AWS Secrets Manager |
| Go service | `cmd/`, `internal/`, `pkg/` | `*_test.go` co-located | Struct with `envconfig`; validate in `main()` | `bin/` (gitignored) | env vars; Vault |
| React SPA | `src/` | `src/**/__tests__/` or `tests/` | `.env.production`, `.env.development`; REACT_APP_ prefix | `build/` (gitignored) | Build-time: public vars only |
| Shared library | `src/` or `lib/` | `tests/` | No runtime env vars | `dist/` (published via registry) | N/A; consumers manage secrets |
| Monorepo | `packages/*/src/` | `packages/*/tests/` | Per-package; workspace-level shared config | `packages/*/dist/` (gitignored) | Per-deployment unit |

# Required Day-One Checklist

```
Repository initialization checklist:

Source & Structure:
  ✓ Every top-level folder has a documented purpose (README or OWNERS)
  ✓ Test layout mirrors source layout
  ✓ Generated artifacts gitignored (dist/, build/, __pycache__/, node_modules/)
  ✓ No src/ installed directly as runtime content without a build step

Configuration:
  ✓ .env.example committed with placeholder values only
  ✓ Startup fails fast with clear error if required env vars are missing
  ✓ No hardcoded URLs, credentials, or environment-specific values in source
  ✓ Secrets scanner (detect-secrets / git-secrets) installed as pre-commit hook

Build & Verification:
  ✓ One-command setup documented in README (e.g., make dev-setup)
  ✓ Build command produces identical output from same source (reproducible)
  ✓ Lint, format, test commands runnable from clean checkout
  ✓ CI pipeline runs all verification commands on pull request

Dependencies:
  ✓ Lockfile committed (package-lock.json, poetry.lock, go.sum, Cargo.lock)
  ✓ License policy documented (approved + prohibited licenses)
  ✓ Automated dependency vulnerability scanning enabled (Dependabot, pip-audit)

Documentation:
  ✓ README: purpose, prerequisites, setup, environment variables, key commands
  ✓ docs/adr/ initialized (first ADR: project initialization decisions)
  ✓ CODEOWNERS or OWNERS file defining review responsibilities
  ✓ Monorepo only: module graph, affected-test policy, cache key inputs, generated file policy, and workspace tooling documented
```

# Selection Rules

Select this capability when **repository structure and foundational engineering conventions** are the primary decision. Route here for monorepo initialization, workspace layout, devcontainer/reproducible local environment, onboarding-time targets, generated-file policy, and day-one build/test conventions. Route elsewhere when: **module-boundary-design** is primary (internal package boundary decisions within an already-initialized repository); **secret-configuration-security** is primary (auditing or securing an existing project's configuration management); **ci-cd** is primary (pipeline automation behavior and deployment workflow design for an existing repository); **containerization** is primary (Dockerfile, container image structure, and OCI artifact design for an existing project).

# Proactive Professional Triggers

Use this capability proactively, even when the request does not ask for project initialization:

- **Signal:** a new repository, package, service, SDK, workspace, devcontainer, or monorepo package is created with folders before architecture is named. **Hidden risk:** arbitrary scaffolding becomes a permanent ownership and module-boundary tax. **Required professional action:** map every top-level folder to runtime, deployment, test, documentation, or ownership responsibility before accepting the layout. **Route to:** `project-initialization`, `module-boundary-design`, and `architecture-style-selection`. **Evidence required:** folder map, owner, rejected folders, module graph, and unresolved decisions.
- **Signal:** setup instructions depend on oral knowledge, external docs, local machine state, or manual environment steps. **Hidden risk:** first-checkout verification fails and onboarding debt becomes invisible until the team grows. **Required professional action:** require one-command setup, documented prerequisites, toolchain pins, and clean-checkout validation. **Route to:** `project-initialization`, `execution-trajectory-analysis`, `validation-broker`, and `quality-test-gate`. **Evidence required:** bootstrap command, validation command output, README location, toolchain file, and remaining manual step.
- **Signal:** templates, project memory, previous repos, generated scaffolds, or AI-generated plans are reused as the initialization basis. **Hidden risk:** stale conventions, personal preferences, or unsupported patterns can override the current repository purpose and platform policy. **Required professional action:** compare memory/template assumptions against current graph, owner, runtime, deployment, and compliance constraints. **Route to:** `project-memory-governance`, `repository-graph-analysis`, `technology-stack-selection`, and this capability. **Evidence required:** template source/date, accepted/rejected assumptions, current convention scan, and residual unknowns.
- **Signal:** `.env.example`, fixture config, docs, generated files, or bootstrap scripts are introduced. **Hidden risk:** secrets, environment-specific values, generated artifact drift, or non-reproducible setup can enter the repository on day one. **Required professional action:** enforce placeholder-only config, generated artifact policy, gitignore coverage, secret scanning, and startup config validation. **Route to:** `secret-configuration-security`, `package-dependency-management`, `containerization`, and this capability. **Evidence required:** scanned paths, placeholder values, gitignore entries, lockfile policy, and secret-scan command.
- **Signal:** the project is a library/SDK, monorepo, extracted service, regulated system, or deployable production service. **Hidden risk:** initialization can silently create public compatibility, migration, compliance, and release obligations before feature work starts. **Required professional action:** define versioning, ownership, data classification, migration path, release gates, and specialist handoffs before scaffolding is considered complete. **Route to:** `api-contract-design`, `delivery-release-gate`, `security-privacy-gate`, `package-dependency-management`, and this capability. **Evidence required:** compatibility policy, data classification, release gate, migration owner, and handoff list.

# Reference Loading Policy

- **L1:** Use only this `SKILL.md` for routing, rejecting arbitrary folder creation, or asking for missing initialization evidence.
- **L2:** Load `references/checklist.md` when drafting or reviewing a real initialization plan, monorepo/workspace scaffold, clean-checkout setup, generated-file policy, or repository reset.
- **L3:** Load `examples/example-output.md` when producing a user-facing initialization plan or when the output contract shape is unclear.
- **L4:** Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when initialization depends on current conventions, prior templates, command output, generated artifacts, or validation freshness.
- **L5:** Pair only the selected specialist gate: `module-boundary-design`, `technology-stack-selection`, `secret-configuration-security`, `package-dependency-management`, `containerization`, `api-contract-design`, or `delivery-release-gate`; do not load unrelated domain references for simple scaffolding rejection.

# Risk Escalation Rules

Escalate when: initialization affects multiple services being initialized simultaneously (shared conventions must be agreed across teams before individuals proceed); the project will handle regulated data (HIPAA, PCI DSS, GDPR) — data classification and access control must be designed before the first line of application code; the project is a shared library or SDK that will be published to a package registry (API stability commitments and semantic versioning strategy must be agreed at initialization); or the new repository is being extracted from an existing system with active users (migration path, old endpoint deprecation, and dual-running period require additional planning).

# Critical Details

- **README as the engineering contract.** The README is not marketing — it is the engineering contract between the project and every engineer who will work on it. A README that does not explain how to run the project locally, what environment variables are required, and what the key verification commands are forces oral knowledge transfer. Oral knowledge is not scalable. README must be updated with every non-trivial structural change.
- **`.gitignore` is a security control, not just housekeeping.** A committed `node_modules/` directory can contain vulnerable versions of dependencies that bypass `npm audit` (which audits `package.json`, not `node_modules/`). A committed `.env` file with real credentials is a credential leak. Treat `.gitignore` entries for secrets and build artifacts as security requirements.
- **Monorepo requires workspace-level tooling decisions before initialization.** A monorepo with 10 packages using different linting configurations, different test runners, and different build tools is not a monorepo — it is 10 loosely related projects in one folder. Before initializing a monorepo: agree on a workspace manager (npm workspaces, Turborepo, Nx, Pants, Bazel); agree on shared lint/format/test tooling; agree on build caching strategy. The complexity of a monorepo is only justified when the coordination benefits (atomic cross-package changes, shared tooling, single CI pipeline) outweigh the tooling overhead.
- **Build cache correctness is more important than cache hit rate.** Cache keys must include lockfiles, toolchain versions, compiler config, generated source inputs, environment-affecting config, and test fixtures. A fast stale build is a correctness defect.
- **Generated files need an ownership rule.** Decide which generated files are committed, ignored, regenerated in CI, or checked for drift. Mixed policy creates review noise and unreproducible builds.
- **Onboarding time is a DevEx metric.** A reproducible local environment (devcontainer, Nix, asdf, mise, toolchain files, or equivalent) should target a clean checkout to passing verification in a measured time window.
- **Documentation targets must be defined at initialization, not added retrospectively.** `docs/runbooks/`, `docs/adr/`, `docs/api/` — each documentation type serves a different audience (operations, architects, consumers). Retroactively adding documentation to an undocumented project requires reconstructing decisions that were obvious at initialization time. Start the first ADR on day one (even if it is minimal), and define the `docs/` structure in the repository charter.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `utils/`, `helpers/`, `common/` top-level folders | No architectural boundary; becomes a dumping ground for unrelated code | Name by domain or ownership: `billing/`, `auth/`, `shared-primitives/`; document boundary |
| `.env` committed with real database password | Credential in git history (permanently, even if deleted in later commit) | Add `.env` to `.gitignore` before first commit; use `.env.example` with placeholders |
| Test folder `tests/misc/` with no relationship to source | Tests cannot be located for specific source modules; orphaned tests accumulate | Mirror source structure: `src/orders/` → `tests/orders/` |
| `README.md` says "see Confluence for setup" | Setup docs rot; Confluence is not versioned with the code | Embed all setup steps in README; Confluence is for architecture/strategy, not setup instructions |
| `dist/` committed to repository | 10MB+ binary artifacts in git; merge conflicts on build output; inflated clone size | Add `dist/` to `.gitignore`; CI builds and publishes artifacts |
| Database credentials in `config/database.yaml` committed | Credentials leak via repository; visible in `git log` permanently | Use environment variable; `config/database.yaml.example` with placeholder |

# Failure Modes

- New engineer joins, clones repository, runs `npm start` — fails with "missing DATABASE_URL environment variable" — no setup documentation; required env vars undocumented; 2-hour debugging session on day one.
- `src/` folder installed directly as runtime content without a build step — production runs uncompiled TypeScript via `ts-node` in a Docker image; startup time 8 seconds; transpilation errors only visible at runtime.
- Three months after initialization, `src/` directory contains: `api/`, `models/`, `utils/`, `helpers/`, `common/`, `misc/`, `temp/`, `old/`, `new/` — no boundary discipline enforced at initialization; refactoring cost now exceeds initial setup time.
- API key committed in `tests/fixtures/integration_config.json` — repository is public; key scraped by secret scanning bots within 15 minutes; AWS account compromised.
- Monorepo initialized without workspace tooling — 8 packages, each with separate `npm install`; CI time 45 minutes; no shared cache; engineers duplicate `eslint.config.js` and `jest.config.ts` in every package.
- Generated `dist/` committed to repository — git clone is 800 MB; engineers pushing build output create merge conflicts on generated files; PR diffs include 40,000 lines of minified JS.

# Output Contract

Return a project initialization plan with:

- `repository_charter` (purpose; owning team; deployment target; regulated data classification if applicable)
- `boundaries_inspected` (existing repository conventions, organization templates, runtime/deploy targets, generated artifact policy, CI, docs, and ownership surfaces reviewed)
- `graph_memory_execution_validation` (current repository graph, prior decisions/templates, command history, and validation evidence accepted or rejected with freshness limits)
- `folder_map` (every top-level folder with documented architectural purpose; depth justified)
- `source_layout` (source entry points; module naming convention; ownership boundaries)
- `test_layout` (mirrors source; test categories: unit, integration, e2e; location of each)
- `configuration_surfaces` (required environment variables with descriptions; validation at startup; `.env.example` template)
- `build_commands` (setup, build, lint, format, test, validate — runnable from clean checkout)
- `dependency_policy` (license allowlist; lockfile strategy; vulnerability scanning tool)
- `secrets_strategy` (secrets scanner pre-commit hook; runtime injection method; prohibited patterns)
- `gitignore_entries` (generated artifacts; local secrets; platform files)
- `documentation_targets` (README sections; `docs/adr/` first entry; CODEOWNERS)
- `ci_pipeline_sketch` (jobs: lint, test, build, security scan; trigger conditions)
- `initialization_to_validation_map` (each scaffold decision mapped to setup command, build/test/lint check, secret scan, docs proof, or specialist gate)
- `monorepo_build_policy` (module graph, workspace manager, affected tests, incremental build tool, cache key inputs, generated file policy, full-test fallback)
- `local_dev_environment` (devcontainer/Nix/asdf/mise/toolchain pins, bootstrap command, onboarding time target)
- `unresolved_decisions` (module boundaries, deployment topology, or tooling choices deferred to named capabilities)
- `evidence_limits` (unverified commands, unavailable org policy, unknown deployment target, stale template assumptions, or unresolved owner)

# Quality Gate

The initialization is complete only when:

1. Every top-level folder has a documented architectural purpose.
2. A clean-checkout, one-command setup is documented and tested.
3. No secrets, credentials, or environment-specific values are in any committed file.
4. Secrets scanner installed as pre-commit hook and CI gate.
5. Test layout mirrors source layout.
6. `.gitignore` covers all generated artifacts and local secrets.
7. Required environment variables documented in `.env.example` with descriptions and placeholder values.
8. Startup fails fast with a clear error if required environment variables are missing.
9. Lockfile committed; license policy and dependency vulnerability scanning enabled.
10. README contains purpose, prerequisites, setup steps, environment variables, and key commands — no reference to external oral knowledge.
11. Monorepos define module graph, workspace tooling, affected-test policy, cache key inputs, generated-file policy, and full-test fallback.
12. Reproducible local environment and onboarding time target are documented and testable.
13. Repository graph, current conventions, prior templates, and project memory are inspected and accepted/rejected with dates or freshness limits.
14. Initialization-to-validation map links each scaffold choice to a command, file, owner, doc location, or specialist handoff.
15. Evidence limits state what was not verified, what remains unresolved, and the next gate before feature work.

# Evidence Contract

The plan must name `boundaries_inspected`, validation commands or artifacts, what evidence proves, what evidence does not prove, residual risk, and the next handoff gate. Clean-checkout setup evidence proves only the documented platform, toolchain, and commands; it does not prove production deployment, all future module boundaries, or organization-wide compliance unless those gates were selected. If current graph, project memory, template source, or execution evidence is missing, return a deferred initialization plan with the smallest next verification step.

# Benchmark Coverage

Use external repository-layout guides and language conventions as starting points only. Approval requires matching the target repository's runtime, deployment, ownership, test strategy, generated artifact policy, dependency policy, and validation commands.

# Routing Coverage

When selected by a router, report which adjacent capabilities were loaded or intentionally skipped: `module-boundary-design`, `technology-stack-selection`, `architecture-style-selection`, `secret-configuration-security`, `package-dependency-management`, `containerization`, `api-contract-design`, `delivery-release-gate`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker`.

# Used By

- delivery-release-gate

# Handoff

Hand off to `module-boundary-design` for internal package boundary decisions within the initialized repository; `secret-configuration-security` for security review of configuration management; `ci-cd` for detailed pipeline automation design; `package-dependency-management` for workspace dependency and lockfile policy; `containerization` for Docker and container image structure; `delivery-release-gate` when initial deployment or release gates are part of the scaffold.

# Completion Criteria

The capability is complete when **any engineer can clone the repository, run one setup command, and have a working development environment with all verification commands passing, every scaffold decision is mapped to current graph/memory/execution evidence, and no secret, credential, or environment-specific value is stored in any committed file**.
