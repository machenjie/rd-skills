# May 2026 Professional Coverage Audit

Audit date: 2026-05-23
Branch baseline: master
Stage: 0 - baseline only

## Stage 0 Scope

This audit records the current repository baseline before any professional
coverage changes. Stage 0 does not change runtime profile counts, add
capabilities, or alter registry count structure.

The validation evidence below confirms the current declared system health. It
does not upgrade static specs into execution-backed proof.

## Inventory Baseline

- Professional skills: 19
- Foundation capabilities: 100
- Domain extensions: 7

## Current Mainline Coverage

The current trunk covers the following professional lanes through registered
professional skills, foundation capabilities, and domain extensions:

- Intake, impact analysis, acceptance criteria, and task DAG planning.
- UX and experience modeling, frontend engineering, and backend engineering.
- Domain modeling, architecture review, data/API contracts, and data middleware.
- Security/privacy, quality/testing, reliability/observability, delivery/release,
  and documentation readiness.
- AI, Web3, mobile, big data, IoT/embedded, payment/trading, and low-level
  systems domain extensions.
- Language capabilities, including TypeScript, Python, Java/JVM, Go, Rust,
  C/C++, Shell/CLI, SQL, and cross-language runtime/testing/performance rules.

Capability registry group counts at this baseline:

- architecture-design: 7
- backend-engineering: 8
- cross-cutting-safety: 1
- data-api-contracts: 6
- data-middleware: 8
- delivery-platform: 5
- domain-modeling: 6
- engineering-workflow: 7
- experience-design: 5
- frontend-engineering: 6
- intake-requirements: 6
- interface-contracts: 2
- language-professional-usage: 8
- quality-testing: 7
- reliability-operations: 6
- security-privacy: 6
- technology-selection: 6

## Validation Chain Result

The full minimum validation chain was run from the repository root on
2026-05-23.

| Command | Result |
|---|---|
| `python3 scripts/validate-skills.py` | Passed: validated 19 professional skill(s). |
| `python3 scripts/validate-capabilities.py` | Passed: validated 100 foundation capability(s). |
| `python3 scripts/validate-domain-extensions.py` | Passed: validated 7 domain extension(s). |
| `python3 scripts/validate-registry.py` | Passed: registry references are valid. |
| `python3 scripts/eval-routing.py` | Passed: 10 golden case(s) passed all checks. |
| `python3 scripts/validate-codegen-benchmarks.py` | Passed: validated 7 benchmark(s). |
| `python3 scripts/build.py --profile recommended` | Passed: built 19 professional skill(s), 100 compiled foundation capability reference(s), 7 domain extension(s), and 19 OpenAI API zip(s). |
| `python3 scripts/build.py --profile full` | Passed: built 19 professional skill(s), 100 compiled foundation capability reference(s), 7 domain extension(s), and 26 OpenAI API zip(s). |
| `python3 scripts/build.py --profile dev` | Passed: built 19 professional skill(s), 100 compiled foundation capability reference(s), 7 domain extension(s), and 126 OpenAI API zip(s). |
| `python3 scripts/validate-installation.py` | Passed: validated 8 runtime root(s), 1368 built skill directory(s), and 171 zip(s). |

## Current Findings

- Body-linked capability references are not fully consistent. Several
  professional skill bodies include generic Reference Loading Policy examples
  such as `42-idempotency-retry-design.md` and
  `82-solution-optimality-evaluation.md` even when those capability files are
  not compiled into that skill's `references/capabilities/` directory. Example:
  `acceptance-criteria-builder` links the example paths, but its compiled
  recommended references currently contain only `04-scenario-decomposition.md`,
  `05-acceptance-standard-definition.md`, and `index.md`.
- Routing evaluation remains a static specification check. `scripts/eval-routing.py`
  validates schemas, registry references, declared risk triggers, gates, and
  rule-derived expectations; it does not invoke an agent or compare live router
  output to golden results.
- Codegen benchmark validation remains definition-focused. `scripts/validate-codegen-benchmarks.py`
  validates benchmark structure, required files, headings, route hints, and
  registry references; it does not execute starter repositories or test suites.
- Several horizontal professional knowledge domains still need strengthening in
  later phases. Candidate areas include deeper accessibility, performance,
  dependency/supply-chain review, data governance, migration operations, and
  contract/runtime execution evidence.

## Freeze Rules

Stage 0 freezes the current baseline:

- Do not change profile counts.
- Do not add capabilities.
- Do not change registry count structure.
- Do not install `src/` or raw `src/registry` content as runtime content.
- Treat this document as an audit baseline, not a coverage expansion.

