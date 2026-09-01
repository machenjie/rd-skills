# Runtime Build

rd-skills has one Runtime build. This filename is retained for link
compatibility; it does not define a selectable Profile dimension.

The source inventory is 1 Control, 25 Professional, 150 Foundation, and 13
Domain Skills: 189 total and 188 non-Control. The Runtime exposes 26 top-level
Skills: 1 Control and 25 Professional. Foundation and Domain Skills never enter
Host top-level discovery.

| Runtime surface | Count | Delivery |
| --- | ---: | --- |
| Control | 1 | top-level Skill |
| Professional | 25 | top-level Skill and Primary Route owner |
| Product Foundation | 141 | capability modifiers compiled behind Professional selectors |
| Domain | 13 | `modifier-only` Layer 3 items compiled behind Professional selectors |
| Authoring/internal Foundation | 9 | source and routing-validation inventory only |

The resulting Runtime delivery is 26/154/9
top-level/targeted/routing-only entries. The source Layer 3 catalog contains
163 entries. Nothing is deleted to reduce Host-visible Skill count: all 150
Foundation and 13 Domain sources remain governed and validated.

The fixed request path is:

```text
User -> engineering-control-plane -> Primary Professional
     -> selector -> 0..3 JIT Layer 3 -> required References
```

Primary Professional routing happens once. Task and Review assignments consume
Main's bound route and do not rerun the global router. They open only the
capsule-named Layer 3 items and necessary Targeted References; no consumer opens
the complete Foundation/Domain catalog or a Layer 3 index as runtime context.

## Compatibility Name And Manifests

Build output remains under `dist/**/recommended/`, and manifests retain
`profile: recommended` for compatibility with existing paths and installations.
That internal name is fixed. It is not an install, package, doctor, marketplace,
or runtime-discovery choice. New `full` or `dev` output is rejected, and a build
removes only preflighted retired output directories inside its managed roots.

The build manifest records the complete Foundation and Domain source inventory,
Foundation scopes, the 154 compiled candidates, 9 routing-only entries,
Professional ownership, and `compiled_layer3_format: ai-consumption-v1`.
Manifests also include the authoritative host matrix and an
`authoritative_build_inputs` snapshot. That snapshot binds the complete `src/`
tree, `scripts/validation_utils.py`, `pyproject.toml`, and every producer script
named by Core, using normalized path, type, byte length, and content. Generated
outputs and caches are excluded. Packaging, installation, upgrade, and OpenAI
bundle validation recompute the same file-set digest and reject missing,
malformed, or stale input. Git HEAD and source-scoped clean/dirty/unavailable
state remain audit metadata rather than source-fingerprint inputs.

## Layer 3 Projection

Compiled companions are AI-consumption projections, not copies of authoring
roots. A Foundation projection keeps its complete decision boundary,
high-value rules, anti-patterns, stop conditions, and Targeted References. A
Domain projection keeps its decision boundary, professional rules, gotchas,
stop/escalation conditions, and Targeted References. Generic inputs,
checklists, and output scaffolding remain outside the compact projection.

The built Professional root carries the JIT entrypoint. A selected nested
Reference is opened only by its explicit logical path. Compiled references do
not change top-level Skill counts, and generated indexes are validation aids,
not catalogs to preload.

The Reference inventory contains 611 registry-indexed Markdown files and 612
physical Markdown files. Exactly 1 physical Reference is unindexed: the
Foundation authoring template Reference.

Retiring the development Runtime does not retire its proof obligations.
`scripts/validate-built-skill-reference-links.py` projects all 163 Foundation
and Domain sources once into a cleaned temporary directory outside the
repository and `dist/`. It checks source/registry agreement, compact projection
shape, selector ownership and reachability, nested files and links, symlink
containment, the 154 Runtime JIT entries, and the 9 non-Runtime authoring entries.

## Preserved Routing Semantics

Runtime consolidation does not change Primary, Layer 3, Domain positive/anti,
role-authorization, or Review routing. Ordinary Android and iOS/iPadOS work uses
the successor platform Domains; obsolete mobile identifiers remain unsupported
and are not redirected. Cross-platform framework work requires the
cross-platform Domain plus every concrete target-platform Domain established by
repository and release evidence.

Installed-client source and lifecycle work remains owned by
`installed-client-change-builder`; browser/PWA-only work remains frontend work.
Infrastructure source remains owned by
`platform-infrastructure-change-builder`; production apply, release, and
rollback remain delivery-gate decisions.

## Runtime Versus Agent Profiles

Runtime is the Skill-discovery and JIT-delivery surface described above. Agent
Profiles are the four fixed execution roles: main control, analysis, task, and
review. Codex, Claude, and Copilot builds emit those four host-native files.
Cline and OpenAI API receive the Runtime Skills without a claim of native Agent
Profile enforcement. A change to Runtime composition must not add an Agent
Profile, Execution Level, or runtime state machine.

The Copilot delivery family has three independent static Host Surfaces:
Copilot CLI, Copilot VS Code, and Copilot Coding Agent. Their declared tool and
external-read delivery may differ, while the shared generated Profile stays a
portable superset. The Task Agent invokes the tools actually delivered by the
current Host within the static Role, Task Contract, sandbox, and tool boundary.
The build does not infer an invocation capability state or a fallback Host
Executor. Actual tool, permission, sandbox, and required-artifact failures are
reported from the attempted operation with the current real Task ID.

## Growth Rule

Place new knowledge in this order:

1. an existing Targeted Reference;
2. an existing Foundation or Domain Skill;
3. an existing Professional Skill;
4. a new Professional Skill.

A framework, library, protocol, platform sub-capability, scenario, or gotcha is
not by itself a new top-level Skill. Add a Professional Skill only when the
capability has a stable, independent Primary Route and clear task ownership.
Use [Skill content governance](SKILL_CONTENT_GOVERNANCE.md#layer-rules) for the
cross-layer placement contract.

Build with `python3 scripts/build.py`. Generated manifests are the inventory
authority; do not hand-edit generated projections or fingerprints.
