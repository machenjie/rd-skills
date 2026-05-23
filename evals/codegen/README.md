# Code Generation Benchmarks

This directory contains benchmark definitions for evaluating whether an
agent can produce professional code on realistic product engineering tasks.
The routing golden cases prove that ChangeForge selects the right skills;
these code generation benchmarks define the implementation quality evidence
expected after a real change is attempted.

The benchmarks are static specifications. They do not invoke an agent or
model. A benchmark runner can materialize each `starter-repo/`, apply the
`prompt.md`, execute the `test-suite/`, run the `security-checks/`, and score
the result with `review-rubric.md`.

## Layout

Each benchmark lives under one product surface category:

```text
evals/codegen/
  backend/
  frontend/
  data-api/
```

Each benchmark directory must contain:

```text
prompt.md
starter-repo/
expected-qualities.yaml
test-suite/
security-checks/
review-rubric.md
```

The validator also requires `README.md` inside each child directory so the
starter state, tests, and security checks remain reviewable even before a
runner exists.

## Running

```bash
python3 scripts/validate-codegen-benchmarks.py
```

The validator checks that the benchmark set is complete, every required file
exists, markdown files contain the required sections, and
`expected-qualities.yaml` references real ChangeForge skills, capabilities,
domain extensions, and quality gates.

## Authoring Rules

- Use realistic implementation tasks with explicit acceptance evidence.
- Keep starter state small enough for deterministic review.
- Include happy path, negative path, edge case, regression, and failure-mode
  checks in the test suite.
- Include security and privacy rejection cases even when the benchmark does
  not require a full security gate.
- Score code on behavior, safety, maintainability, tests, and evidence rather
  than style preferences alone.