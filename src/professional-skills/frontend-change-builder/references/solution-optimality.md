# Solution Optimality Self-Check — Frontend Change Builder

Compiled from foundation capability `solution-optimality-evaluation`. Apply to every
frontend change that touches a rendering path, state model, data-fetching strategy, or
user-interaction critical path. Loaded on demand per the skill's Reference Loading Policy.

**Three-Challenge Rule** — answer all three before finalizing any frontend design:
1. **Why this approach?** State the concrete reason (not "it felt right" or "it's the common pattern").
2. **Is this the simplest sufficient design?** Local `useState` before context; context before a global store; plain `fetch` before a caching library. Use the simplest layer that satisfies the requirement.
3. **What is the strongest alternative, and why is it rejected?** Name it. Reject it with a specific cost ("adds 180ms INP regression", "requires prop drilling 4 levels", "bundle adds 120KB gzipped").

**Performance Dimension Checklist** — evaluate each or declare N/A with a one-line rationale:

| Dimension | Required Question | Frontend-Specific Failure Mode |
|---|---|---|
| **CPU** | Is there expensive computation on the main thread (sorting, filtering, transforming large arrays) that should be memoized or moved to a Web Worker? Is a component re-rendering unnecessarily on every parent update? | Heavy sort/filter in render function without `useMemo`; entire component tree re-renders on unrelated state change |
| **Memory** | Are event listeners removed on component unmount? Are timers cleared? Is a subscription unsubscribed? Are refs to large objects cleared when no longer needed? | `addEventListener` without `removeEventListener` on unmount accumulates across route changes; `setInterval` not cleared leaks indefinitely |
| **Network** | How many API calls does this user action trigger? Is the response payload bounded (pagination, field projection)? Is stale-while-revalidate used to avoid waterfall fetching? Are assets code-split so unused routes don't block initial load? | Sequential fetch waterfall instead of parallel; unpaginated list endpoint returning 10,000 records; entire app bundle blocking initial render |
| **Disk** | Is `localStorage` / `IndexedDB` usage bounded? Are large assets (images, fonts) cached with appropriate cache headers? Is the service worker cache strategy correct for offline use? | `localStorage` growing unbounded; large images served without CDN caching; service worker caching stale API responses indefinitely |
| **Locks / Contention** | Are concurrent React state updates batched correctly (React 18 automatic batching)? Is a race condition possible between two async operations updating the same state (last-write-wins problem)? | Two in-flight fetch requests resolve out of order — stale response overwrites fresh response; non-batched state updates cause multiple re-renders per event |
| **TPS / QPS** | How many API requests does this feature generate per second at peak usage? Is there debounce or throttle on search input, scroll handlers, or resize handlers? | Unbounced search input fires a request on every keystroke; scroll handler fires 60×/s without throttle |
| **Parallelism** | Are independent API calls fetched in parallel (`Promise.all`) rather than sequentially? | Sequential `await fetch(a); await fetch(b)` adds both latencies instead of running in parallel |
| **Concurrency** | Is the component's async state transition safe if the user navigates away before the request completes? Is an in-flight request cancel handled (AbortController)? | State update on an unmounted component; stale closure captures outdated value after re-render |
| **Response Latency** | Do Core Web Vitals meet budget on a simulated median-device profile (Lighthouse 4× CPU slowdown, simulated 4G)? Does the interaction meet INP < 200ms? Is the critical render path (LCP element) above the fold and not render-blocked? | LCP element loaded lazily; render-blocking CSS or synchronous JS in `<head>`; INP > 200ms due to long task on click handler |
| **Rendering Speed** | Is main thread work per task < 50ms (Long Tasks)? Are expensive child components wrapped in `React.memo` / `v-memo`? Is layout thrashing (read offsetWidth then write style in a loop) prevented? | Synchronous style reads and writes in a loop force repeated layout recalculations; missing memoization causes 200-node subtree re-render on text input |

**Additional Professional Considerations for Frontend Code:**
- **Bundle size discipline**: `main.js` ≤ 150KB gzipped; per-route chunk ≤ 50KB gzipped. Use Webpack Bundle Analyzer or `bundlesize` to enforce this in CI — not as a manual review step.
- **DevTools verification required for critical paths**: For any component on the LCP path or interaction path, run Chrome DevTools Performance tab and Lighthouse before submitting for review. "It feels fast" is not evidence.
- **Re-render cost audit**: Use React DevTools Profiler or Vue DevTools to confirm that state updates do not cascade through unrelated component subtrees. Memoization without measurement is noise; memoization with measurement is optimization.
- **Memory leak patterns**: Route change without cleanup, global event bus without unsubscribe, third-party SDK that retains DOM references, and Web Sockets not closed on unmount are the four most common frontend memory leak sources.
- **Core Web Vitals are not optional**: LCP < 2.5s, INP < 200ms, CLS < 0.1 measured at P75 on field data. These affect SEO ranking and user retention. Lighthouse lab measurements are a minimum bar, not a final validation.
