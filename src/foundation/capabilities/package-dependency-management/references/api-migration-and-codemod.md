# API Migration and Codemod

- Derive old-to-new API and semantic mappings from the target version's official migration guidance.
- Compare defaults, errors, cancellation, resource lifetime, configuration, and serialization behavior.
- Match symbols, types, or AST structure; distinguish identical names from identical bindings.
- Inspect aliases, re-exports, generated code, reflection, and configuration references.
- Separate mechanical rewrites, judgment-dependent changes, and forbidden automatic transformations.
- Run the transformation again against its accepted result.
- Verify that the second run preserves the first result.
- Scan for old API references, mixed versions, unsupported adapters, and skipped files.
- Validate runtime behavior after compilation, especially changed defaults and lifecycle semantics.
- Stage compatibility-sensitive migrations and define rollback across code, configuration, and package artifacts.

| Failure control | Required observation |
|---|---|
| Unrelated symbol shares an API name | Unrelated binding remains unchanged |
| Codemod runs twice | Second result is byte-equivalent or semantically unchanged by the declared contract |
| Types pass but default error behavior changed | Behavioral test exposes the new failure path |
| Alias or generated consumer still uses the old API | Residual scan names the consumer and migration decision |
| Old and new versions coexist | Mixed-version boundary passes its compatibility contract |
