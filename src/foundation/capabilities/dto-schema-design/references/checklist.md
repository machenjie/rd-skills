# DTO Schema Design Checklist

- Define DTO name, direction, and contract owner.
- Define every field type, meaning, and serialization format.
- Mark required, optional, nullable, defaulted, deprecated, and read-only fields.
- Define validation rules and error mapping for invalid input.
- Define mapping to domain or persistence models without leaking internals.
- Include examples for missing, null, default, boundary, and invalid values.
- Define compatibility rules for added, removed, renamed, or changed fields.
- Confirm sensitive internal fields are excluded.
- Define schema or contract tests.
