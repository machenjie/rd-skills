# Vulkan Synchronization and Layouts

Load for Vulkan stage/access dependencies, queue ownership, resource layouts, or submission lifetime.
Skip non-Vulkan paths and GPU changes without Vulkan synchronization or layout decisions.

## Decision Rules

- Bind Vulkan version, enabled extensions, queue families, and device capabilities to the affected path.
- Identify each resource producer and consumer, including host access and presentation.
- Choose synchronization scope from actual pipeline stages and access types.
- Distinguish execution ordering from memory availability and visibility.
- Track image layout and queue-family ownership through the complete resource transition.
- Use barriers, semaphores, and fences for their actual dependency and completion scopes.
- Preserve buffer/image lifetime until all dependent submissions finish.
- Validate descriptor, shader, format, stride, and alignment compatibility for the selected pipeline.
- Handle failed submission or device loss without treating affected output as complete.
- Combine validation-layer evidence with captures and independent image or numeric comparisons.

- When artifacts change, pair shader/kernel identity with asset content, compile options, and interface/layout versions.
- Invalidate affected cached pipelines or compiled artifacts using the actual API and hot-reload contract.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Write precedes read on another queue | Required execution, visibility, and ownership dependencies hold |
| Image is used after a layout transition | Actual layout matches the next access |
| Host destroys a resource after enqueue | Lifetime extends through dependent device use |
| Validation reports no errors but colors differ | Image oracle still determines correctness |
| Device capability differs on another target | Feature and synchronization assumptions are checked independently |

| Old shader/kernel is paired with new asset content or layout | Incompatible or stale artifacts are rebuilt or rejected before their result is accepted |

## Proof Limits

- A Vulkan validation run covers exercised paths and enabled checks; it does not establish Metal or WebGPU correctness.

## Sources

- [Vulkan synchronization guide](https://docs.vulkan.org/guide/latest/synchronization.html)
