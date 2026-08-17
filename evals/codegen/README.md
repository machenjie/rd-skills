# Code Generation Benchmarks

This directory contains benchmark definitions for evaluating whether an
agent can produce professional code on realistic product engineering tasks.
The routing golden cases prove that rd-skills selects the right skills;
these code generation benchmarks define the implementation quality evidence
expected after a real change is attempted.

The static validator checks benchmark definitions. The execution runner has two
modes:

- Without a candidate implementation, it performs smoke checks that benchmark
  setup, test, and security scripts can run from the starter repo and that
  expected command documentation matches those scripts.
- With a candidate implementation, it runs the benchmark scripts against that
  implementation directory so real behavior and security assertions can fail or
  pass the generated code.

## Layout

Each benchmark lives under one product surface category:

```text
evals/codegen/
  backend/
  frontend/
  data-api/
  security/
  integration/
  data-middleware/
  reliability/
  delivery/
  ai/
  web3/
  payment/
  mobile/
  bigdata/
  iot/
  low-level/
  code-elements/
  devex/
  logging/
  pressure/
  review/
  validation/
  structure/
  performance/
  finops/
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

The definition validator requires `README.md` inside each child directory so
the starter state, tests, and security checks remain reviewable. The execution
runner additionally requires `starter-repo/setup.sh`, `test-suite/run.sh`, and
`security-checks/run.sh`.

## Running

```bash
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
```

The definition validator checks that the benchmark set is complete, every
required file exists, markdown files contain the required sections, and
`expected-qualities.yaml` references real rd-skills skills, capabilities,
domain extensions, and quality gates.

The default `--limit` path selects assertion-backed cases first, validates the
checked-in setup/test/security harness, and executes the real assertions as a
negative control against the intentionally incomplete starter. A smoke case
fails if its starter unexpectedly passes every product assertion. Candidate
mode never executes a candidate-supplied setup or test script. It does execute
candidate code through the checked-in harness and assertions, using a minimal
environment and a sanitized temporary snapshot. Environment filtering is not
an operating-system sandbox: run candidate mode only in a disposable container
or VM with no mounted credentials or sensitive host data.

To evaluate a generated implementation for one benchmark, apply the generated
code to a copy of that benchmark's `starter-repo/` and pass that directory:

```bash
CHANGEFORGE_RUN_CODEGEN_CANDIDATE=1 \
python3 scripts/run-codegen-benchmarks.py \
  --benchmark security/ssrf-url-allowlist \
  --candidate-dir /path/to/generated/ssrf-url-allowlist
```

To evaluate multiple generated implementations, arrange them under
`<candidate-root>/<category>/<benchmark>/` and pass `--candidate-root`.
Candidate mode still runs the benchmark harness first, then runs real assertion
files such as `test-suite/tests/test_behavior.py` and
`security-checks/security_tests/test_security.py` when the benchmark supplies
them. A benchmark without real assertion files is rejected in candidate mode
instead of being reported as evaluated from smoke checks alone.

## Authoring Rules

- Use realistic implementation tasks with explicit acceptance evidence.
- Keep starter state small enough for deterministic review.
- Include happy path, negative path, edge case, regression, and failure-mode
  checks in the test suite.
- Include security and privacy rejection cases even when the benchmark does
  not require a full security gate.
- Score code on behavior, safety, maintainability, tests, and evidence rather
  than style preferences alone.
