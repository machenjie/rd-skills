# Data Format Contract Usage Checklist

- Identify the format surface: content type, schema file or registry, generated model, storage file, parser config, and owning team or module.
- Record schema authority: source file, registry mode, generated artifact status, runtime validator, fixture owner, and migration owner when relevant.
- Record parser contract: library, version, options, safe/unsafe mode, duplicate-key behavior, unknown-field behavior, coercion, null/default/empty/zero/false semantics, and size/depth limits.
- Classify compatibility: backward, forward, full, transitive, additive, breaking, or storage-only; name affected consumers and stored data.
- Review format-specific hazards: Protobuf field numbers and reserved values, YAML 1.1/1.2 scalar coercion, TOML type strictness, XML XXE/canonicalization, CSV formula injection, JSON duplicate keys, CPE normalization, Avro/Parquet reader-writer behavior.
- For CPE, record the governing specification version plus accepted bindings and forms.
- For CPE 2.3, parse or unbind to logical attributes while preserving `ANY`, `NA`, wildcard, escaped-literal, missing, and malformed distinctions.
- Verify form-specific quoting and escaping, form-defined attribute count and wildcard placement, and normalization defined by the selected specification or contract.
- Compare source and target component by component, record the version relation and each other attribute relation, then apply the selected overall-match decision without inventing lexical version ordering.
- Exercise malformed input, escaping, `ANY`/`NA`, normalization, match/non-match, version, and bind-unbind-bind round-trip fixtures; state inspected forms, commands, proof limits, and residual risk.
- Record generated artifact policy: source spec, generator version/config, output path, committed/ignored decision, and drift command.
- Define fixtures: positive, negative, golden, parser differential, malformed hostile input, old-reader/new-writer, old-data/new-reader, and absent/null/default/unknown-field cases as needed.
- Route security review for untrusted parser input, unsafe loaders, XXE, formula cells, duplicate-key privilege decisions, deserialization, or unbounded payloads.
- Validate with the smallest command or artifact that can fail for the changed format boundary, then state what it proves and does not prove.
- Treat repository inspection, prior task evidence, old examples, previous parser output, and generated artifacts as selectors only until current source/schema/parser evidence confirms them.
