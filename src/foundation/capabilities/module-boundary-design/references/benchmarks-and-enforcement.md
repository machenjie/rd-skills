# Module Boundary Enforcement And Proof

These patterns compare enforcement mechanisms and bound static, generated, dynamic, and runtime proof for changed module edges.

## Enforcement Choice

| Boundary risk | Mechanism | Evidence and limit |
| --- | --- | --- |
| Internal import or private-type reach-through | Language or package visibility, explicit exports, an import rule, or an architecture test. | Proves covered source edges; reflection, generated code, dynamic loading, and runtime calls need separate inspection. |
| Accidental public-surface growth | Export or API diff, consumer inventory, compatibility review, and contract tests. | Covers inspected consumers and tested semantics; unknown external consumers remain a stated risk. |
| Source or generated dependency cycle | Dependency graph plus a cycle check over authored and generated sources. | Proves the scanned graph; service locators, callbacks, plugins, and network cycles may remain outside it. |
| State or storage bypass | Contract-level integration tests, write/read-path scan, and access-control checks where available. | Covers exercised paths; ad hoc queries, operator access, and uninspected runtimes remain outside the proof. |
| Temporary exception | Narrow rule with reason, owner, affected edges, removal condition, and review date. | Records accepted debt; it does not establish that the crossing is safe or permanent. |

## Boundary Evidence Record

- Name the boundary-kind, authoritative mechanism, enforcement owner, responsibility, invariant or policy authority, state/source authority, and accountable reviewer.
- Record public exports and consumers, private internals, allowed and forbidden edges, and the cycle-check source and result.
- Record enforcement location and command, generated or dynamic surfaces inspected, exceptions, migration/rollback, and residual unknowns.

## Official Sources

Official sources were accessed on 2026-07-26.

- [Go language specification](https://go.dev/ref/spec)
- [Go: How to Write Go Code](https://go.dev/doc/code)
- [Bazel repositories, packages, and targets](https://bazel.build/versions/7.4.0/concepts/build-ref)
- [Bazel visibility](https://bazel.build/versions/8.5.0/concepts/visibility)

## Proof Limits

The Go specification establishes package blocks, file blocks, imports, exported identifiers, and import-cycle constraints; it does not prescribe a repository's semantic owner or general directory layout. Go's code-layout guidance is tool and module guidance, not proof that a directory owns a domain rule. Bazel defines packages through `BUILD` files, targets and dependency labels, while visibility enforces who may depend on a target. Bazel does not prove domain ownership, runtime/service boundaries, dynamic edges, external SDK compatibility, or untracked consumers.
