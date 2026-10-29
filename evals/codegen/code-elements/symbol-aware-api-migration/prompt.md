# Benchmark Prompt

## Task

Implement `migrate(source)` in `subject.py` for this deterministic migration harness. Use the fictional contract below. Do not build a general codemod engine.

## Context

`legacy_api.fetch` and `current_api.fetch` both return `str`. Both accept one positional key and keyword policies `strict` and `release`. Imports have no side effects in this fixture. Old defaults are both true; new defaults are both false. Strict missing reads raise `LookupError`; permissive reads return an empty string. Release closes the acquired resource.

## Requirements

- Resolve flat module imports and direct `fetch` aliases. Migrate only the legacy symbol. Preserve unrelated same-spelling calls, strings, comments, and explicit policies.
- Move the import to `current_api` while retaining its local binding. Insert missing old defaults at each confirmed call. Use UTF-8 byte offsets when applying AST spans.
- Support single-line calls with one positional key. Function scopes, rebinding, function-value exports, unsupported imports, and dynamic keyword arguments require manual judgment. Leave the entire input unchanged when any such target use is unresolved.
- Return `source`, `changed_calls`, and an `unresolved` reason list. Scan the returned source for `residual_import_lines` naming the legacy module and `mixed` old/new imports. The scan is import-level evidence; opaque configuration and downstream re-exports remain unproved.
- Preserve repeated-run idempotence. Invalid Python raises `ValueError`. Transform strings only; never write a file. Retaining the original input supplies this fixture's rollback boundary.
- Compare runtime values, errors, and release traces. Successful compilation and unchanged return annotations cannot approve a semantic change.

## Constraints

Use Python standard-library AST facilities and bounded fixture input. Run no network, package manager, shell, or production migration. Generated sources, reflection, arbitrary scopes, real libraries, and staged repository rollout require separate evidence.

## Deliverables

Implement the callable and state unresolved references and proof limits. Do not widen the supported language subset to hide uncertainty.

## Completion Evidence

Run the passing candidate and reject the incomplete starter plus the unrelated-symbol faulty control. Exercise aliases, shadows, non-ASCII offsets, defaults, errors, cleanup, residual imports, and repeat execution.
