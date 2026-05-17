# Contract Testing Checklist

- Identify providers, consumers, contract surface, and schema source.
- Verify success, error, auth, pagination, nullability, default, and version behavior.
- Include examples that represent supported consumer expectations.
- Check backward compatibility or document approved breaking change path.
- Validate events, webhooks, or schemas with machine-readable checks where possible.
- Run provider verification in CI before release.
