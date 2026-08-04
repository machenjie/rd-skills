# AI Review Checklist

- Verify imports, APIs, methods, config keys, and generated file paths exist.
- Compare patterns against nearby code.
- Identify hidden assumptions and invented contracts.
- Report each reachable issue with source evidence, impact, and an outcome-based correction direction.
- Keep review mode non-mutating and leave implementation choices to the owning task agent.
- Treat clone mechanisms as candidates until task-specific semantic-equivalence tests cover the accepted value domain and runtime boundary; otherwise report the evidence gap.
- Review type safety, null handling, and error handling.
- Check dependency additions and package scripts.
- Confirm generated tests exercise real behavior.
- Report the safe correction boundary, rollback constraints, and unverified behavior.
- Record findings by severity with file and line evidence.
