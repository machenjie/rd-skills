# Build Tool Evidence Patterns

## Required Evidence

- Tool and target: command, target name, package/module, and config file.
- Graph evidence: declared inputs, outputs, dependencies, generated sources, and affected consumers.
- Generator evidence: source spec, generator version, generated output, and drift command.
- Cache evidence: local/remote cache mode, action-key inputs, nondeterminism review, and cache bypass when needed.
- Artifact evidence: path, checksum/digest, build command, source ref, and provenance/signing status when relevant.

## Tool Permission Boundary

Classify build commands as read-only analysis, generated-output write, cache write, artifact write, package download, or release publish. State whether the command writes to HOME, global caches, network resources, `dist/`, or source directories.

## Handoff Shape

```
Build Tool Usage Record
- Build surface:
- Graph boundary:
- Generated policy:
- Cache contract:
- Artifact contract:
- Validation:
- Residual risk:
```

## Blocking Conditions

Block completion when generated outputs lack authority, a target depends on undeclared inputs, CI/local commands differ without explanation, release artifacts lack path/digest evidence, or validation writes outside the allowed sandbox without disclosure.
