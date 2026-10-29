# Server/Client Rendering Contracts

**Reference type:** targeted
**Load when:** Server rendering, hydration, server/client data transfer, streaming, or server actions affect frontend behavior.
**Do not load when:** The edit changes only CSS or copy without rendering, request-state, or server-entrypoint decisions.
**Required by:** task-agent
**Required output:** boundary-decision, validation-plan, proof-limit

## Boundary Decisions

- Bind the framework, router, runtime, and versions. Locate execution for each render, loader, action, cache, and effect.
- Keep browser-only APIs behind a client execution boundary. A module import can execute before the guarded component body.
- Validate transferred data against the actual server/client serialization contract. Live resources, hidden authority, and unsupported object identities violate that boundary.
- Make the server output and first client render agree. Bind initial time, randomness, locale, and timezone to consistent inputs when they affect markup.
- Distinguish initial hydration from later client updates. Browser screenshots after effects run can miss a broken first render.
- Create request-specific application state per request. Module singletons can retain one user's state for another request.
- Derive cache identity and lifetime from the inputs that change authorized content. A correct query cannot repair an incomplete cache key.
- Treat server actions as independently reachable server entrypoints. Validate input and authorization there, including when the page was already authorized.
- Define post-header streaming errors in terms of partial delivery and resource cleanup outcomes.
- Propagate cancellation to the resources owned by the abandoned stream when supported. Confirm their terminal state at the actual runtime boundary.
- Fix the divergent input or boundary before suppressing hydration warnings or disabling server rendering.

## Distinguishing Checks

| Scenario | Observable check |
| --- | --- |
| Server and browser use different timezones or clock values | Initial markup agrees under the selected input policy |
| Two tenants request the same route concurrently | Neither shared state nor cached content crosses the tenant boundary |
| Unsupported value crosses server/client serialization | The boundary rejects it or transfers an explicit supported representation |
| Client disconnects during a stream | Owned resources finish or cancel without being stranded |
| Invoke a server action without visiting its page | The action enforces its own input and authorization contract |
| Hydrate before client effects execute | Mismatch remains observable instead of being hidden by later updates |

Return execution locations, serialization and cache identities, hydration evidence, and untested deployment conditions.
One route's browser rendering does not establish server isolation or streamed failure behavior.

## Version Sources

- Check [React hydration](https://react.dev/reference/react-dom/client/hydrateRoot), [Vue SSR isolation](https://vuejs.org/guide/scaling-up/ssr.html), or the selected framework's equivalent contract.
- For Next.js server entrypoints, verify the target release's [data security guidance](https://nextjs.org/docs/app/guides/data-security).
