# Build Profiles

Build profiles control which standard Skills are exposed at the top level. They
do not change the control architecture. The source inventory is 1 Control, 26
Professional, 150 Foundation, and 13 Domain Skills: 190 total and 189
non-Control.

| Profile | Top-level Skills | Targeted companions | Routing-only entries | Composition | Use |
| --- | ---: | ---: | ---: | --- | --- |
| `recommended` | 27 | 154 | 9 | 1 Control + 26 Professional | normal project or user installation |
| `full` | 40 | 141 | 9 | recommended + 13 Domain | Domain discovery at the top level |
| `dev` | 190 | 0 | 0 | 1 Control + 26 Professional + 150 Foundation + 13 Domain | rd-skills authoring and debugging |

The current second-phase expansion adds 2 Professional and 6 Foundation Skills
plus 22 References without changing Domain membership. `recommended` compiles the 141
registry-owned `product` Foundation Skills and the 13 automatically routable
Domain candidates into the Professional Skills that name them. Its 1
`authoring-only` and 8 `dev-only` Foundation Skills remain routing-only.
`full` compiles the same 141 Foundation Skills while exposing all 13 Domain
roots at the top level; its 9
non-product Foundation Skills remain routing-only. `dev` exposes all 150
Foundation and 13 Domain Skills at the top level and does not compile companion
Layer 3 copies. The build manifest records every Foundation scope, the compiled
Foundation and Domain sets, each routing-only entry, the authoritative companion
or top-level path, and `compiled_layer3_format: ai-consumption-v1`.
The source Layer 3 catalog contains 163 entries.
The Reference inventory contains 611 registry-indexed Markdown files and 612
physical Markdown files. Exactly 1 physical Reference is unindexed: the
Foundation authoring template Reference.

Compiled companions are AI-consumption projections, not copies of authoring
roots. A Foundation projection keeps the title, complete `Skill Role` as
`Decision Boundary`, High-Value Rules, Anti-Patterns, Stop Conditions, and
Targeted References. A Domain projection keeps the title, complete `Role` as
`Decision Boundary`, Professional Decision Rules, High-Value Gotchas, Stop /
Escalation Conditions, and Targeted References. Routing triggers, generic
inputs, execution checklists, and output contracts remain outside the compiled
projection. `full` still exposes complete Domain authoring roots, and `dev`
still exposes complete Foundation and Domain authoring roots.

The built Professional `SKILL.md` links a compact discovery/validation index so
generated companions remain root-reachable, but task execution opens only the
capsule-named Layer 3 root. When a deterministic evaluation fixture explicitly
names a nested Reference as `owner/references/file.md`, the context evaluator
loads exactly that one file from either the compiled companion directory or the
top-level owner. It never opens the Layer 3 index, scans a directory, or follows
links recursively. Compiled references do not change top-level Skill counts and
their indexes must not be read as catalogs.

Ordinary Android and iOS/iPadOS routing uses their successor platform Domains.
The obsolete mobile Domain and compatibility mode have been removed. Removed
legacy Skill ids are unsupported and are not redirected.

Installed-client source and lifecycle work belongs to
`installed-client-change-builder`; browser/PWA-only work remains frontend work.
Infrastructure source belongs to `platform-infrastructure-change-builder`;
production apply, release, and rollback remain delivery-gate decisions.
Cross-platform framework work requires the cross-platform Domain plus every
concrete target-platform Domain established by repository and release evidence.

Codex, Claude, and Copilot builds emit four Agent Profile files: main control,
analysis, task, and review. Cline and OpenAI API packaging receive standard Skills
but no claim of native Profile enforcement. Manifests include the authoritative
host matrix and an `authoritative_build_inputs` snapshot. That snapshot binds the
complete `src/` tree, `scripts/validation_utils.py`, `pyproject.toml`, and the
exact producer scripts named by Core
`principle_acceptance_contract.producers[*].argv[1]` (including
`scripts/build.py`) by normalized path, type, byte length, and content;
generated outputs and caches are excluded. Packaging, runtime installation,
upgrade, and OpenAI bundle validation recompute the same file-set digest and
reject missing, malformed, or stale snapshots. Git HEAD and source-scoped
clean/dirty/unavailable state are audit metadata only, so a final commit that
contains both source and its generated artifacts does not invalidate otherwise
identical inputs. Current supported hosts declare isolated workspaces unsupported
and Utility no-edit prompt-enforced; Claude/Copilot review omits command execution
because safe read-only semantics are unsupported.

Use the canonical build commands in [Installation](INSTALLATION.md#build).
Generated manifests are the authoritative record of profile and package
contents. A profile name is a packaging choice, not a risk mode or task state.
