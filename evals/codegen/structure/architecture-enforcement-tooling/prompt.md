# Benchmark Prompt

## Task

Add enforcement for existing module-boundary rules that currently exist only in an architecture document.

## Context

The starter repository has `domain` importing `api`, UI importing persistence code, cycles between modules, broad public exports, and generated clients that need exceptions. Reviews mention the rule but CI does not check it.

## Requirements

- Define import boundary, cycle detection, public/private export, forbidden dependency, lint, type-check strictness, dead code, and complexity rules that apply.
- Choose language-appropriate tooling such as ArchUnit, Dependency Cruiser, import-linter, eslint boundaries, go vet, or staticcheck.
- Add a CI command and clear failure examples.
- Define generated-code exclusions and migration path.
- Assign rule ownership and residual unenforced rules.

## Constraints

- Do not leave architecture enforcement as documentation only.
- Do not add rules without a runnable CI gate.
- Do not break generated code without exception policy.
- Do not rely on manual code review as the only enforcement mechanism.

## Deliverables

- Architecture Enforcement Plan.
- Tool choice and CI command.
- Failure examples and generated-code exceptions.
- Migration path and owner.

## Completion Evidence

- CI can fail on at least one representative forbidden dependency or cycle.
- Generated-code exceptions are scoped and documented.
- Residual unenforced rules are named.
