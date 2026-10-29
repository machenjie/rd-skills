# Scene Assets and Save Migration

Load for scene transitions, asset lifetime, asynchronous loading, save compatibility, or recovery.
Skip game changes that preserve scene, artifact, and persistent-state contracts.

## Decision Rules

- Assign scene objects, assets, subscriptions, and asynchronous loaders an owner and lifetime.
- Cancel or reject completion from a scene generation that has already unloaded.
- Keep asset identifiers and content versions compatible with the state that references them.
- Distinguish reusable asset caches from mutable per-scene or per-player state.
- Validate saved schema, game version, and required assets before activating restored state.
- Migrate saves using explicit version transitions and preserve recovery from interrupted conversion.
- Check that repeated migration cannot apply the same state transformation twice.
- Define the treatment of removed items, renamed fields, and unsupported future save versions.
- Preserve accepted player progress when loading fails or falls back to a previous save.
- Exercise memory and frame impact during scene replacement, streaming, and repeated load/unload.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Old scene load completes after transition | Result cannot repopulate the unloaded scene |
| Asset version changes under an existing save | Compatibility is checked before use |
| Save migration stops midway | Recovery preserves the last accepted state |
| Migration repeats after restart | State is not upgraded twice |
| Future save version is opened by an older build | Unsupported state is rejected without destructive overwrite |
| Scene repeatedly loads and unloads | Owned resources do not accumulate |

## Proof Limits

- Storage success does not establish that a save restores valid gameplay state or compatible assets.
