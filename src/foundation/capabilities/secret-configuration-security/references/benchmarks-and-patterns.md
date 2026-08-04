# Secret Configuration Security Exposure And Rotation Patterns

Load this reference when multiple exposure paths or rotation mechanisms are plausible and the root rules do not select a safe lifecycle.

## Exposure Paths

| Path | Easy-to-miss failure | Decision evidence |
| --- | --- | --- |
| Source and history | Deletion hides current text but leaves clones, forks, generated files, or retained history. | Path/history scope, scanner limits, credential authority, containment, and rotation record. |
| CI and build | Masking misses transformed values; caches, artifacts, metadata, or untrusted jobs retain material. | Event and runner trust, permissions, representative logs, cache/artifact scope, and rebuild plan. |
| Client artifacts | Public config, bundles, source maps, static HTML, or cached releases cross the server trust boundary. | Build-prefix rules, inspected artifacts, CDN/source-map scope, and version retirement. |
| Observability and support | Object serialization, traces, crash reports, exports, or debug tools fan out access. | Safe-field policy, representative payload tests, sink audience, retention, and deletion owner. |
| Secret store or KMS | A managed store still permits broad decrypt, unsafe deletion, or unaudited break-glass. | Principal/operation scope, audit source, recovery window, and emergency authority. |
| Backups and offline consumers | Old values remain usable after online services rotate. | Consumer inventory, backup policy, job cadence, adoption/revoke criteria, and residual copies. |

## Rotation Sequence

1. Inventory known consumers and select adoption signals without exposing the raw value.
2. Introduce the new version and compatibility window required by the protocol.
3. Move consumers in an order that preserves service and authorization behavior.
4. Verify adoption and failure signals before revoking the old version.
5. Revoke or contain old material, then clean history, images, logs, caches, or support artifacts as a separate recovery action.

## Evidence Safety

- Refer to labels, versions, redacted policy fields, or approved fingerprints; keep raw values out of retained evidence.
- Treat a scanner miss as scoped detector evidence, not proof that provider validity, history, or external sinks are clean.
- Route image, pipeline, logging, runtime config, and release implementation to their owning Skills.
