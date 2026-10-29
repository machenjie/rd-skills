# Vue Reactivity and Effect Lifetime

**Reference type:** targeted
**Load when:** Vue reactive tracking, watcher timing, component identity, or effect disposal affects current behavior.
**Do not load when:** The edit changes only CSS, copy, or business logic without reactive or lifecycle decisions.
**Required by:** task-agent
**Required output:** decision-record, validation-plan, proof-limit

## Decision Rules

- Bind the Vue version and actual Composition or Options API path before choosing a lifecycle mechanism.
- Preserve the intended reactive source when destructuring or copying values. A detached snapshot can silently lose required reactivity.
- Use computed state for derivation.
- Use watchers when a change needs synchronization with an external effect.
- Choose `watch` for explicit sources and `watchEffect` for automatic tracking. `watchEffect` tracks dependencies read during synchronous execution.
- Match watcher flush timing to the observed state or DOM. Do not infer post-update DOM from the default scheduling mode.
- Associate cleanup with the watcher run that acquired the resource. Invalidate obsolete requests before their results can update current state.
- Use `onWatcherCleanup` only where the target version supports it. Vue 3.5+ requires registration during synchronous watcher execution, before an `await`.
- Own watchers created in asynchronous callbacks explicitly. They may lack the component binding that stops synchronous setup watchers on unmount.
- Stop detached effect scopes when their owner ends. A hidden view and a destroyed component may have different lifetimes.
- Bind component keys to the product's reset policy, avoiding unintended state transfer between reordered items.

## Failure Scenarios

| Scenario | Observable check |
| --- | --- |
| Two queries complete in reverse order | Stale query results leave current state unchanged |
| Create a watcher after an asynchronous callback, then unmount | The explicit stop path removes the watcher and its resources |
| Read reactive state only after an await in `watchEffect` | The test exposes the missing tracked dependency |
| Read DOM before and after an update | The selected flush mode observes the required phase |
| Dispose a detached scope twice | Cleanup preserves the resource owner's valid terminal state |

Return the reactive source, scheduling choice, cleanup owner, and remaining timing limits.

## Version Sources

- Check watcher scheduling, tracking, and cleanup against the target version's [Vue watcher guide](https://vuejs.org/guide/essentials/watchers.html).
- Do not translate React Effect rules into Vue rules by name alone.
