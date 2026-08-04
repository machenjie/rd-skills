# Language Idiom Evidence Patterns

Use this reference when idiom-enforcement closure depends on repository convention evidence, validation freshness, prior source or task evidence claims, AI-generated symbol verification, tool permission boundaries, or changed-idiom-to-validation mapping. Keep it as an evidence map, not a language tutorial.

## Changed-Idiom-To-Validation Map

| Idiom claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Local convention is known | Existing nearby examples, formatter/linter config, language version, and owner convention inspected | The review is anchored in current repository practice | Uninspected packages, generated code, or older branches use the same style |
| Public API follows language idiom | Changed signature, naming, visibility, doc-comment format, error/result/nullability contract, and consumer impact inspected | The covered public surface follows the selected convention | Unknown consumers, semver rollout, or generated SDK adoption are safe |
| Runtime boundary is validated | Validator location, malformed fixture, denied/invalid test output, and static-type proof limit | External input is checked at the inspected boundary | Every producer, legacy payload, or production shape is covered |
| Resource/concurrency lifecycle is idiomatic | Acquisition site, owner, cleanup/cancel path, race/leak/cancel command, and residual interleaving risk | Covered lifecycle paths follow target runtime idiom | All scheduler timings, load patterns, or sibling paths are safe |
| Dependency/helper is idiomatic | Reuse scan, standard-library alternative, existing dependency check, license/security signal, and placement rationale | The helper or dependency has a reviewed reason to exist | Future maintainers will not need consolidation or removal |
| AI-generated code is verified | Symbol/import search, installed-version check, compiler/typecheck/lint output, and behavior test | Named AI-generated symbols and idioms are valid for the current toolchain | Uninspected generated blocks or runtime-only paths are correct |

## Evidence Quality Labels

- **Strong evidence**: current source and local convention examples inspected after final edit, command or artifact named, exit code or review status recorded, and proof limit stated.
- **Weak evidence**: generic style guide, old review note, prior claim, formatter-only output, or examples outside the changed surface.
- **Missing evidence**: no language/runtime version, no local convention example, no validation command, no malformed fixture for runtime boundary, or no owner for exception.
- **Invalid evidence**: copied blog pattern, unverified AI symbol, static type used as runtime proof, generated artifact trusted without source, or stale command after final idiom edit.

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, prior reviews, generated docs, and old command output as discovery inputs until current source, installed versions, and validation confirm them.
- Accept a prior "this is idiomatic", "formatter passed", "API is stable", or "AI code was reviewed" claim only when language version, config, changed files, generated artifacts, and command output still match.
- Mark evidence stale after edits to public API signatures, error/result models, validators, resource lifecycle, concurrency primitives, formatter/linter config, generated code, dependency versions, or test fixtures.
- Map every accepted idiom claim to a current command, typecheck, lint, formatter, test, static analysis, local example, owner approval, or explicit not-run residual risk.

- If dependency install, code generation, fixture refresh, or formatter rewrite, record source of truth, generated output owner, diff review, rollback path, and package/version boundary.
- If live service, production data, cloud console, package publishing, or security scanner export, require permission, redaction, retention limit, rollback or no-write proof, and stop condition.
