# Open Source Benchmark Map

Use this reference to anchor code-element review in professional public standards without turning the capability into a language tutorial.

## Benchmark Sources

### isocpp/CppCoreGuidelines

- Absorbed professional ideas: initialize objects before use, make ownership and lifetime visible, prefer RAII for resource cleanup, avoid surprising control flow, and treat fallthrough or unchecked state as review-significant.
- Target reference file(s): [variables.md](variables.md) for initialization, lifetime, aliasing, and ownership; [statements.md](statements.md) for RAII, cleanup, fallthrough, and ordering.
- What must not be copied or over-applied: do not copy guideline text into this capability, and do not apply C++ lifetime rules to languages with different ownership models. Route language-specific behavior to `language-idiom-enforcement` and the relevant language/runtime capability.

### google/eng-practices

- Absorbed professional ideas: code review should verify correctness, readability, maintainability, focused tests, and smallest-sensible change scope before approval.
- Target reference file(s): [variables.md](variables.md), [expressions.md](expressions.md), and [statements.md](statements.md) for local review questions and evidence expectations.
- What must not be copied or over-applied: do not turn broad review philosophy into automatic rejection of every nontrivial line. Use it to require evidence where a local variable, expression, or statement can change behavior.

### google/styleguide

- Absorbed professional ideas: names, constants, comparisons, exceptions, cleanup constructs, and file-local declarations should follow language and repository convention.
- Target reference file(s): [variables.md](variables.md) for naming, mutability, and constants; [expressions.md](expressions.md) for comparisons, coercion, and magic values; [statements.md](statements.md) for exception and cleanup statement shape.
- What must not be copied or over-applied: do not make one language's style guide a global rule. Prefer repository convention and language-specific capabilities when syntax, naming, or runtime semantics differ.

### airbnb/javascript

- Absorbed professional ideas: prefer explicit defaulting semantics, avoid hidden coercion in material logic, keep expressions reviewable, and make mutation or side effects visible.
- Target reference file(s): [expressions.md](expressions.md) for truthiness, nullish/default behavior, coercion, and side-effect purity; [variables.md](variables.md) for `const`/mutation ownership and scope.
- What must not be copied or over-applied: do not enforce JavaScript style as a universal rule, and do not treat subjective formatting preferences as capability gates. Route JavaScript runtime details to `language-idiom-enforcement`.

### rust-lang/api-guidelines

- Absorbed professional ideas: API-facing values should make ownership, error states, optionality, and invariants explicit rather than hiding them behind ambiguous defaults.
- Target reference file(s): [variables.md](variables.md) for `Option`/`Result`-like state clarity, ownership, mutability, and lifetime; [expressions.md](expressions.md) for explicit error/default handling; bridge references when the issue is actually API shape.
- What must not be copied or over-applied: do not treat Rust-specific ownership syntax as a rule for other languages, and do not let this local capability own public API design. Escalate API shape to `implementation-structure-design` or data/API capabilities.

### ryanmcdermott/clean-code-javascript

- Absorbed professional ideas: name meaningful decisions, avoid excessive expression complexity, avoid hidden side effects, and keep functions/conditionals easy to review.
- Target reference file(s): [expressions.md](expressions.md) for named predicates, complex conditionals, and side-effect purity; [variables.md](variables.md) for concept-specific naming; [statements.md](statements.md) for visible main flow.
- What must not be copied or over-applied: treat Clean Code material as subjective heuristics, not hard gates. Do not reject code only because it disagrees with a preference when repository convention and tests support the local choice.

### wemake-services/wemake-python-styleguide

- Absorbed professional ideas: avoid mutable defaults, overly complex expressions, ambiguous names, broad exception handling, and hidden control-flow surprises in Python code.
- Target reference file(s): [variables.md](variables.md) for mutable defaults, naming, and lifetime; [expressions.md](expressions.md) for expression complexity and coercion; [statements.md](statements.md) for exception scope and cleanup.
- What must not be copied or over-applied: do not import Python-only lint rules into other languages, and do not make every strict linter preference a product-quality blocker. Escalate Python semantics to `language-idiom-enforcement`.

## Mapping Rules

- Use a benchmark as an anchor for the professional expectation, not as a substitute for repository-specific evidence.
- Prefer the repository's language/runtime capability when a benchmark points to language-specific behavior.
- Prefer `quality-test-gate` when the benchmark implies executable proof, such as nullish defaults, fallthrough, cleanup, or transaction ordering.
- Prefer `security-privacy-gate` when the element controls trust boundaries or sensitive data.

## Review Prompts

- Which public standard or local rule makes this variable, expression, or statement risky?
- Is the risk local enough for this capability, or does it require language, structure, side-effect, or security ownership?
- What test, static analysis, typecheck, or review artifact proves the intended element behavior?
