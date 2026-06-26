---
name: package-dependency-management
description: Use when governing package managers, lockfiles, dependency additions, upgrades, removals, transitive changes, license compatibility, provenance, supply-chain risks, security scanning, and runtime compatibility across languages.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "88"
changeforge_version: 0.1.0
---

# Mission

Govern package-manager choice, lockfile discipline, dependency addition / upgrade / removal, transitive risk, license compatibility, provenance, supply-chain integrity, vulnerability scanning, and runtime compatibility across languages. Treat every dependency as a permanent operational liability whose cost (CVE patching, license review, transitive graph audit, build-time impact, deploy-target compatibility) the team commits to indefinitely. New dependencies are rejected unless the cost is lower than the alternative.

# When To Use

Use when adding, removing, upgrading, downgrading, vendoring, pinning, auditing, or changing dependency resolution; when modifying package-manager behavior, lockfiles, workspaces, monorepo package graphs, build plugins, SDK packages, runtime libraries, or container base images. Use whenever a CVE advisory lands against a current dependency.

# Do Not Use When

Do not use to approve packages "for convenience" when the standard library, an existing approved dependency, or 20-50 lines of local code would solve the problem with lower risk. Do not use for runtime selection (use `language-runtime-selection`).

# Stage Fit

- **Discovery / intake** - state the need, ecosystem, package manager, current dependency graph, alternatives, and affected runtime/deploy targets before package selection.
- **Implementation / review** - inspect lockfile diff, transitive graph, install scripts, license, vulnerability status, generated outputs, and compatibility tests before merge.
- **Release / operations** - verify SBOM, provenance, advisory SLA, rollout/rollback impact, and exception ownership before production exposure.
- **Maintenance / cleanup** - reassess stale dependencies, vendored forks, EOL runtimes, hoisting drift, generated-client drift, and accepted exceptions on a schedule.

# Non-Negotiable Rules

- **New dependencies require justification against alternatives.** Standard library first, language/runtime/native platform feature second, existing repository utility third, already-installed dependency fourth, small local code fifth, and a new dependency only when measurably better with maintenance and supply-chain cost accepted.
- **Lockfile is mandatory for applications and binaries.** `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` / `Pipfile.lock` / `poetry.lock` / `uv.lock` / `go.sum` / `Cargo.lock` / `mvnw + dependency-lock` / `composer.lock` / `Gemfile.lock` / `mix.lock`. Libraries publish ranges; applications pin via lockfile.
- **CI installs use reproducible commands**: `npm ci`, `pnpm install --frozen-lockfile`, `yarn install --immutable`, `pip install --require-hashes` / `uv sync --frozen`, `cargo build --locked`, `go mod download` (with `go.sum` verification), `mvn -B verify`. Plain `npm install` / `cargo update` in CI is rejected.
- **Supply-chain posture is verified before merge**: OpenSSF Scorecard ≥ 5 for new dependencies; install scripts inspected; maintainer count ≥ 2 (or vendor SLA); CVE disclosure process exists; recent release activity within 18 months.
- **License compatibility checked on every add and every major upgrade.** GPL/AGPL/SSPL/BUSL into a permissive product is a license incident.
- **Transitive graph reviewed on add.** A 10-line utility that pulls 200 transitive packages is rejected. Run `npm ls`, `pipdeptree`, `cargo tree`, `mvn dependency:tree`, `go mod graph` and read the output before approval.
- **Install scripts are a supply-chain risk class.** Packages with postinstall / lifecycle scripts (`postinstall` in npm, `build.rs` in Cargo, setup.py side effects in pip) require explicit review; prefer alternatives without install scripts where possible. CI environments use `npm ci --ignore-scripts` plus an allowlist where feasible.
- **SBOM is generated and stored** per release (CycloneDX or SPDX).
- **Vulnerability scan runs in CI and on schedule**: `npm audit --omit=dev`, `pnpm audit`, `pip-audit`, `cargo audit`, `govulncheck ./...`, `mvn org.owasp:dependency-check`, `osv-scanner`, GitHub Dependabot / Renovate. High/Critical advisories block merge unless triaged with documented compensating control.
- **Vendoring is a deliberate choice with rationale** (regulatory air-gap, reproducibility, supply-chain isolation), not the default.
- **Monorepo dependency graphs must preserve module boundaries.** Workspace ranges, hoisting, peer dependencies, generated packages, and shared tooling must not allow packages to import across forbidden boundaries or bypass affected-test selection.
- **Generated package outputs need a version and drift policy.** Generated clients, protobufs, OpenAPI SDKs, ORM clients, or codegen artifacts must declare whether source or output is authoritative and how CI detects stale generation.
- **Current graph, memory, and execution evidence are mandatory.** Dependency decisions must cite current package graph, lockfile diff, package-manager command output, project memory or prior exceptions with dates, and validation freshness.

# Industry Benchmarks

- **OWASP** — A06:2021 Vulnerable and Outdated Components; Component Analysis cheat sheet.
- **NIST SP 800-218 (SSDF)** — PS.3 (archive code), PW.4 (third-party reuse), PW.5 (secure design), RV.1 (vuln identification).
- **OpenSSF Scorecard** — measurable health: maintenance, code-review, branch-protection, dangerous-workflow, pinned-dependencies, vulnerabilities. Threshold: ≥ 5/10 for new adds; ≥ 7/10 for critical dependencies.
- **SLSA** (Supply-chain Levels for Software Artifacts) — provenance and build-integrity levels. Aim for SLSA L2+ for production artifacts.
- **SBOM** — CycloneDX / SPDX standards; generated by syft / cdxgen / `cargo cyclonedx` / `npm sbom`.
- **CVE-2018-1000805 / event-stream incident, CVE-2021-44228 Log4Shell, ua-parser-js hijack, xz-utils backdoor (CVE-2024-3094), tj-actions/changed-files compromise (CVE-2025-30066)** — canonical supply-chain incident references.
- **PEP 668 / PEP 723 / PEP 621** for Python packaging; **TC39 import maps** and Node.js subpath imports for JS; **Cargo features unification** rules; **Maven dependency-mediation** rules; **Go MVS (minimum version selection)** model.

# Selection Rules

Select for any package-manager / lockfile / dependency-add / dependency-upgrade / dependency-removal / license / provenance / install-script / native-extension / transitive-dependency / supply-chain concern. Pair with `dependency-vulnerability-scanning` for CVE depth; with the matching `<lang>-professional-usage` for language-specific tool pins; with `security-privacy-gate` for incident-level supply-chain risk.

Select for monorepos when workspace manager behavior, hoisting, lockfile partitioning, package graph boundaries, generated package outputs, or build cache dependency inputs are part of the change.

### Lockfile / Reproducible-Install Reference

```
Language       | Lockfile                       | Reproducible install command
---------------|--------------------------------|---------------------------------------
npm            | package-lock.json              | npm ci
pnpm           | pnpm-lock.yaml                 | pnpm install --frozen-lockfile
yarn (berry)   | yarn.lock                      | yarn install --immutable
Python (pip)   | requirements.txt + hashes      | pip install --require-hashes -r ...
Python (uv)    | uv.lock                        | uv sync --frozen
Python (poetry)| poetry.lock                    | poetry install --no-update
Go             | go.sum (+ vendor optional)     | go build  (verifies sums automatically)
Rust           | Cargo.lock                     | cargo build --locked
Java (Maven)   | dependency-lock plugin output  | mvn -B verify (with lock plugin)
Java (Gradle)  | gradle.lockfile                | gradle --write-verification-metadata
Ruby           | Gemfile.lock                   | bundle install --deployment
PHP            | composer.lock                  | composer install --no-dev --prefer-dist
Elixir         | mix.lock                       | mix deps.get --only prod
Containers     | image digest (sha256:...)      | docker pull <image>@sha256:...
```

### Add-a-Dependency Rubric

```
1. Is the need already met by standard library? → use stdlib.
2. Is it already met by a native platform/runtime/framework feature? → use native.
3. Is it already met by an existing repository utility? → reuse existing code.
4. Is it already met by an approved installed dependency? → use existing dependency.
5. Is the implementation < 50 LoC of clear code with low bug/security risk? → write it locally.
6. Candidate package check:
   - Maintainer count ≥ 2 (or vendor SLA)
   - Last release within 18 months
   - OpenSSF Scorecard ≥ 5
   - License compatible with project
   - Transitive count + size acceptable (read `<tree>` command output)
   - No install/postinstall script (or explicit review)
   - CVE history reviewed
   - Alternatives compared (≥ 2 candidates)
7. Lockfile updated; CI install command verified reproducible.
8. SBOM regenerated; vulnerability scan green or triaged.
```

# Proactive Professional Triggers

Use this capability proactively, even when the request does not ask for dependency governance:

- **Signal:** a diff changes a package manifest, lockfile, package manager config, workspace config, generated package, container base image, or dependency resolution rule. **Hidden risk:** a small manifest edit can alter transitive code, licenses, install scripts, runtime compatibility, and affected-test selection. **Required professional action:** inspect the dependency graph and lockfile delta before accepting the change. **Route to:** `package-dependency-management`, `dependency-vulnerability-scanning`, `quality-test-gate`, and `validation-broker`. **Evidence required:** manifest diff, lockfile diff, tree command output, affected packages, and validation command.
- **Signal:** a new direct dependency is proposed for convenience, speed, parsing, formatting, SDK access, build tooling, or one small helper. **Hidden risk:** convenience packages add permanent CVE, license, provenance, install-script, and maintenance obligations. **Required professional action:** run the alternatives ladder and reject the dependency unless it beats stdlib/native/existing/local-code options. **Route to:** `minimal-correct-implementation`, `package-dependency-management`, and the matching `<lang>-professional-usage`. **Evidence required:** alternatives considered, candidate comparison, transitive count, maintainer/release health, and owner acceptance.
- **Signal:** project memory, prior exception, old audit output, generated dependency report, or previous Renovate/Dependabot decision is reused. **Hidden risk:** stale memory can preserve expired exceptions, unsupported runtime constraints, or already-fixed advisories. **Required professional action:** compare memory against current graph, advisories, lockfile, and CI execution. **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`, and this capability. **Evidence required:** source date, accepted/rejected memory, current scan output, lockfile freshness, and explicit unknowns.
- **Signal:** dependency change includes native extension, install script, code generation, SDK/client generation, package publishing, peer dependency, hoisting, or container image digest. **Hidden risk:** build behavior, deploy target, generated contract, or runtime artifact can diverge from local tests. **Required professional action:** require target-platform build evidence, generated-file policy, isolated package install/build, and rollback or repin path. **Route to:** `language-runtime-selection`, `sdk-library-contract-design`, `containerization`, `delivery-release-gate`, and this capability. **Evidence required:** target runtime, build output, generated drift check, isolated install/build command, and rollback plan.
- **Signal:** vulnerability, malicious package, license incident, provenance gap, EOL runtime, or high-severity advisory affects the graph. **Hidden risk:** patch urgency can hide exploitability, compatibility, release, or compensating-control gaps. **Required professional action:** separate advisory triage from dependency update mechanics, document exploit path and SLA, and route security/release gates when needed. **Route to:** `dependency-vulnerability-scanning`, `security-privacy-gate`, `delivery-release-gate`, and this capability. **Evidence required:** advisory IDs, exploitability, patched version, scan output, compensating control, owner, and expiration.

# Reference Loading Policy

- **L1:** Use only this `SKILL.md` for routing, rejecting convenience dependencies, or requesting missing lockfile/supply-chain evidence.
- **L2:** Load `references/checklist.md` when drafting or reviewing a real dependency add, removal, upgrade, vendoring decision, generated package policy, lockfile delta, or accepted exception.
- **L3:** Load `examples/example-output.md` when the output contract shape is unclear or a concise dependency decision record is needed.
- **L4:** Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when graph reachability, prior exceptions, command output, generated artifacts, affected tests, or validation freshness determine approval.
- **L5:** Pair only selected specialist gates: `dependency-vulnerability-scanning`, matching `<lang>-professional-usage`, `language-runtime-selection`, `sdk-library-contract-design`, `security-privacy-gate`, `delivery-release-gate`, `containerization`, or `quality-test-gate`.

# Risk Escalation Rules

- Escalate to `security-privacy-gate` for High/Critical CVE without trivial upgrade path, suspected malicious package, credential exposure in dependency, license incident, or SLSA-level regression.
- Escalate to `delivery-release-gate` for major version upgrade with rollout implications (e.g., framework major bump touching all services).
- Escalate to `language-runtime-selection` when the dependency choice implies a runtime shift (e.g., adopting a library that requires a newer language version, or a native extension that constrains deploy target).
- Escalate to `dependency-vulnerability-scanning` for CVE-depth analysis, exploit-path assessment, and patch-prioritization.
- Escalate to `technology-stack-selection` when adding a dependency that crosses a stack boundary (new datastore client, new framework family).

# Critical Details

- **Direct vs transitive impact.** A 10-line utility that pulls 200 transitive packages multiplies your CVE exposure by 200, your license-review burden by 200, and your build-time cost. Read `npm ls` / `cargo tree` / `pipdeptree` / `go mod graph` before approving the add.
- **Lockfile drift kills reproducibility.** A `package-lock.json` regenerated by a different npm version produces a different resolved graph. Pin tooling (.nvmrc / .python-version / rust-toolchain.toml / .tool-versions) so the lockfile is stable across machines.
- **Library vs application packaging differs.** Libraries publish loose version ranges and do **not** check in a lockfile of their dependencies into the published artifact (npm publishes from source, not lock); applications and binaries **must** ship a lockfile.
- **Install scripts are the most common supply-chain attack vector.** event-stream (2018), ua-parser-js (2021), and many npm typosquats exfiltrate via postinstall. `npm ci --ignore-scripts` is a defense; pair with an allowlist for packages that genuinely need build steps (native modules).
- **Cargo features unification** can pull in unintended features through a transitive dependency enabling `default-features` of a shared crate; review the `cargo tree -f "{p} {f}"` output.
- **Maven dependency mediation** picks the nearest version in the graph, which can silently downgrade. Use `mvn dependency:tree -Dverbose` and `<dependencyManagement>` to pin.
- **Go MVS** picks the highest minimum version requested by any module in the graph. Use `go mod why` and `govulncheck` to understand the resulting graph.
- **Container base images are dependencies.** Pin by digest (`sha256:...`), not by tag. Use distroless / minimal images; scan with Trivy / Grype.
- **License classification at minimum**: Permissive (MIT, BSD, Apache-2.0), Weak copyleft (LGPL, MPL, EPL), Strong copyleft (GPL, AGPL), Source-available (BUSL, SSPL, Elastic v2), Proprietary. Project's outbound license dictates which inbound categories are compatible.
- **EOL runtimes are dependency risk.** Running on Node.js 16 (EOL) or Python 3.8 (EOL) is a supply-chain risk regardless of package CVEs because security patches stop arriving.
- **Renovate / Dependabot** are operational hygiene tools. Configure grouping (one PR per ecosystem per week), auto-merge for patch versions of trusted deps with green CI, and SLA for high-severity advisories (e.g., merge or mitigate within 7 days).
- **Workspace hoisting changes runtime reality.** A package may pass locally because a dependency is hoisted to the root, then fail in an isolated publish or deployment. CI must verify package-level install/build where packages are published or deployed independently.
- **Affected-test selection depends on dependency graph accuracy.** If package A consumes generated output from package B, changes to B's schema/source must invalidate A's tests even when A's source files did not change.

# Failure Modes

- **Lockfile-less install** — Symptom: "works on my machine" / different resolved graph in CI vs prod. Cause: missing lockfile or `npm install` instead of `npm ci`. Detection: CI lockfile-check step. Impact: non-reproducible builds, intermittent CVE re-introduction.
- **Tiny package, huge transitive surface** — Symptom: adding `left-pad`-class utility brings 50 transitive packages. Cause: rubric step 4 skipped. Detection: read `<tree>` output during code review. Impact: multiplied CVE exposure, license review burden.
- **Install-script side effect** — Symptom: build downloads from an unverified URL or writes to `$HOME`. Cause: postinstall script unreviewed. Detection: `--ignore-scripts` + manual allowlist; npm/yarn audit of install scripts. Impact: supply-chain compromise.
- **License incident** — Symptom: AGPL transitive introduced into permissive product. Cause: upgrade introduced new dep with stronger copyleft. Detection: FOSSA / scancode / licensee on every PR. Impact: legal/compliance incident, forced removal under deadline.
- **Native extension breaks deploy target** — Symptom: binary built on Linux glibc, deploys to Alpine musl, crashes at start. Cause: native ext not validated against target. Detection: build matrix matches deploy target; container test. Impact: failed deploy, rollback.
- **EOL-runtime CVE backlog** — Symptom: Snyk shows 30+ Highs that can't be patched. Cause: runtime EOL; upstream stopped issuing patches. Detection: runtime lifecycle policy. Impact: forced runtime upgrade under deadline.
- **Major-version upgrade ships unannounced** — Symptom: production breaks on deploy of seemingly minor PR. Cause: Renovate auto-merged major bump. Detection: separate Renovate groups: patch (auto), minor (review), major (manual). Impact: outage.
- **Vendored fork drifts** — Symptom: vendored package missing 18 months of security fixes. Cause: vendoring without an upgrade SLA. Detection: vendored-dep upgrade audit quarterly. Impact: known-CVE exposure.
- **Container image by tag, not digest** — Symptom: build reproducibility lost; supply-chain attack via tag re-tag. Cause: `FROM image:latest` or `FROM image:1.2`. Detection: enforce `@sha256:` in CI. Impact: silent base-image swap.
- **Hoisted dependency masks missing package declaration** — Symptom: package builds in monorepo root but fails when published or deployed alone. Cause: undeclared dependency resolved through root hoist. Detection: isolated package install/build in CI. Impact: broken release artifact.
- **Generated client drift** — Symptom: API schema changed but generated SDK package was not regenerated. Cause: generated-file policy absent. Detection: CI codegen drift check. Impact: consumers compile against stale contract.

# Output Contract

Return a **Dependency Decision Record** containing:
- **Change type** (add / upgrade-major / upgrade-minor / upgrade-patch / remove / replace / vendor)
- **Boundaries inspected** (package manifests, lockfiles, workspace graph, generated outputs, build/deploy target, CI install mode, prior exceptions, and skipped boundaries)
- **Graph / memory / execution validation** (current dependency graph, project memory, advisory/source dates, package-manager command output, scan output, and validation freshness)
- **Need statement** and **alternatives considered** (stdlib / native platform feature / existing repository utility / existing dependency / local code / candidate packages ≥ 2)
- **Selected package(s)** with version pin
- **Justification** against the rubric (rubric steps 1-5 explicitly answered)
- **Lockfile impact** (added / removed / version delta) — link to lockfile diff
- **Transitive impact** — count, new packages introduced, new native deps, build-time delta
- **Module graph impact** — affected packages, workspace edges, peer dependency changes, hoisting risk, generated package dependencies, and affected tests
- **License status** — every new transitive license listed; compatibility verdict
- **Vulnerability status** — scanner output (`npm audit` / `pip-audit` / `cargo audit` / `govulncheck` / `osv-scanner`) — green or triaged with compensating control
- **OpenSSF Scorecard** (for new direct adds) with score
- **Install scripts** — any present? reviewed? allowlisted?
- **Provenance / SLSA level** if applicable; **SBOM regenerated**
- **Compatibility tests** — affected behavior tested (CI links)
- **Generated file policy** — source vs generated authority, drift check command, committed/ignored outputs, cache invalidation inputs
- **Rollout risk** — coordinated upgrade required? release gate involved?
- **Accepted exceptions** with owner, scope, expiration
- **Dependency-to-validation map** — each graph/license/security/runtime/generation/compatibility risk mapped to command, test, scan, or specialist gate
- **Evidence limits** — not-inspected transitive paths, stale advisories, unsupported tooling, skipped platform matrix, or unresolved owner

# Quality Gate

1. Lockfile present and updated; CI uses reproducible install command (no plain `install` / `update`).
2. Rubric trace complete: stdlib / native platform feature / existing repository utility / existing dependency / local code / candidate-comparison answered.
3. Transitive graph reviewed; `<tree>` command output attached.
4. License compatibility verified per-transitive; no incompatible licenses introduced.
5. Vulnerability scan green or every advisory triaged with documented compensating control and SLA.
6. OpenSSF Scorecard ≥ 5 for new direct adds.
7. Install scripts inspected; if present, allowlisted with reviewer name.
8. SBOM regenerated; container images pinned by digest.
9. Compatibility tests cover affected behavior; for major upgrades, integration suite re-run.
10. Renovate / Dependabot grouping & auto-merge policy in place; high-severity advisory SLA defined.
11. Monorepo workspace changes update module graph, affected tests, cache inputs, and isolated package install/build checks.
12. Generated package outputs have drift checks and an explicit committed/ignored policy.
13. Current repository dependency graph and project memory/prior exceptions are inspected with dates and freshness limits.
14. Dependency-to-validation map covers lockfile, graph, license, vulnerability, install script, runtime compatibility, generated output, and behavior tests.
15. Evidence limits state what the dependency evidence proves, what it does not prove, and which gate owns residual risk.

# Evidence Contract

The decision must cite `boundaries_inspected`, validation commands or artifacts, what evidence proves, what evidence does not prove, residual risk, and next handoff gate. Dependency evidence proves only the inspected package graph, lockfile state, package-manager behavior, scans, licenses, and validation commands at that point in time; it does not prove future advisories, every deploy target, downstream consumers, or production behavior unless those gates were selected and verified. Missing current graph, lockfile diff, scan output, or validation freshness blocks approval.

# Benchmark Coverage

Supply-chain frameworks and incident history calibrate risk. Approval requires local graph evidence, package-manager command output, lockfile and generated-output policy, license/vulnerability/provenance checks, and compatibility validation for the target runtime and deployment surface.

# Routing Coverage

When selected by a router, report which adjacent capabilities were loaded or intentionally skipped: `dependency-vulnerability-scanning`, matching `<lang>-professional-usage`, `language-runtime-selection`, `sdk-library-contract-design`, `security-privacy-gate`, `delivery-release-gate`, `containerization`, `quality-test-gate`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker`.

# Used By

security-privacy-gate, delivery-release-gate, project-initialization, ai-code-review-refactor, technology-stack-selection

# Handoff

- **`dependency-vulnerability-scanning`** for CVE-depth analysis, exploit-path, patch prioritization.
- **`security-privacy-gate`** for supply-chain incidents, license incidents, malicious-package detection.
- **`delivery-release-gate`** for upgrade rollout sequencing and rollback triggers.
- **`architecture-impact-reviewer`** for monorepo module boundaries and dependency direction.
- **`quality-test-gate`** for affected-test selection and cache correctness evidence.
- **`language-runtime-selection`** when dependency forces a runtime shift.
- **Matching `<lang>-professional-usage` capability** for ecosystem-specific tool pins and commands.

# Completion Criteria

The dependency change is complete when: it is reproducible (lockfile + CI install command); justified against the rubric; current graph/memory/execution evidence is fresh; transitive / license / vulnerability / scorecard / install-script / SBOM checks are documented; compatibility tests cover affected behavior; rollout risk is named; and any accepted exception has owner, scope, and expiration. Convenience is not a justification.
