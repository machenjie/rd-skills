# Open Source Benchmark Map

Use this reference to anchor code-element review in professional public standards without turning the capability into a language tutorial.

## Benchmark Sources

- Google Engineering Practices: review for readability, maintainability, and correctness at the smallest changed unit.
- CERT C and CERT C++: initialization, lifetime, switch fallthrough, resource cleanup, undefined behavior, and error handling rules.
- C++ Core Guidelines: initialize objects, avoid uninitialized reads, prefer RAII, make ownership explicit, and avoid surprising control flow.
- Effective Go: keep `err` handling explicit, avoid unsafe shadowing, and keep defer/cleanup ownership visible.
- Python professional practice: avoid mutable default arguments, make `None` semantics explicit, and prefer readable expressions over clever comprehensions.
- TypeScript and JavaScript professional practice: distinguish `??` from `||`, avoid coercive equality in material logic, and make truthiness/default behavior explicit.
- SonarSource and similar static-analysis rule sets: empty statements, nested conditionals, magic numbers, cognitive complexity, fallthrough, and resource leaks.
- OpenSSF Scorecard and NIST SSDF: generated code still needs evidence for secure implementation choices, dependency surfaces, and reviewed correctness.

## Mapping Rules

- Use a benchmark as an anchor for the professional expectation, not as a substitute for repository-specific evidence.
- Prefer the repository's language/runtime capability when a benchmark points to language-specific behavior.
- Prefer `quality-test-gate` when the benchmark implies executable proof, such as nullish defaults, fallthrough, cleanup, or transaction ordering.
- Prefer `security-privacy-gate` when the element controls trust boundaries or sensitive data.

## Review Prompts

- Which public standard or local rule makes this variable, expression, or statement risky?
- Is the risk local enough for this capability, or does it require language, structure, side-effect, or security ownership?
- What test, static analysis, typecheck, or review artifact proves the intended element behavior?

