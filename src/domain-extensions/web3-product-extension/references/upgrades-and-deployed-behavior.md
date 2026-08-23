# Upgrades and Deployed Behavior

Use this Reference only for the named decision.

## Decision Rules

- **Use deployed arithmetic semantics**: prove overflow, precision, scaling, rounding, and exceptional arithmetic against the deployed compiler and assets.
- Prove storage-layout compatibility plus authorized and denied initializer or reinitializer behavior for an upgrade.
- Prove migration order and upgrade recovery behavior.
- Record deployed code/configuration identity with distinct proxy-admin and implementation ownership.
- Bind arithmetic, compiler, VM, asset-scale, and rounding semantics to the recorded deployed identity.
