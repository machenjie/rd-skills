# Bridge, Plugin, and FFI Contracts

Load this Reference only when a bridge, plugin, FFI boundary, generated binding,
or shared/native call changes compatibility or failure behavior.

Official framework documentation below was accessed on 2026-07-24.

## Decision Boundary

- Version bridge, FFI, plugin, and generated interfaces; define payload, threading, cancellation, error, and backward-compatibility behavior.
- Pin framework, runtime, plugin, native dependency, generated binding, and
  serialization versions for each target.
- Define payload schema, nullability, ownership, threading, reentrancy,
  cancellation, timeout, error, and unknown-result behavior.
- Keep capability and permission checks on the platform side that can prove
  them; return structured denial and unavailable states to shared code.
- Treat generated or plugin APIs as compatibility contracts across rolling
  upgrades and target-specific implementations.

## Failure Proof

- Exercise malformed payload, native exception, denial, cancellation, timeout,
  process loss, duplicate callback, and incompatible-version paths.
- Test every affected target implementation; one bridge implementation proves
  none of the others.
- Verify release optimization, symbol/linking, plugin registration, and package
  inclusion in release-shaped artifacts.

## Required Record

Return the interface and version contract, thread and ownership model, failure
mapping, target implementations, release proof, and residual risk.

## Primary Sources

- [Flutter platform channels](https://docs.flutter.dev/platform-integration/platform-channels)
- [React Native native modules](https://reactnative.dev/docs/turbo-native-modules-introduction)
- [Electron IPC renderer](https://www.electronjs.org/docs/latest/api/ipc-renderer)
- [Tauri calling Rust from the frontend](https://v2.tauri.app/develop/calling-rust/)
- [Tauri plugins](https://v2.tauri.app/plugin/)

## Source Limits

These pages do not establish repository versions, payload safety, target
implementations, plugin compatibility, runtime registration, or release
artifacts. Verify the pinned toolchain and generated outputs in the task.
