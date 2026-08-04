# Frontend Experience Choice Check

**Load when:** a rendering, state, data-fetching, asset, lifecycle, or interaction-path choice may materially change user experience or browser resource use.

**Do not load when:** the change has no experience/runtime tradeoff, or current design-system and repository patterns already determine the bounded implementation.

Derive thresholds from the current repository baseline, representative device/network/workload, user/business objective, platform policy, and measured evidence; bundle budgets, Core Web Vitals, memoization, workers, and code splitting are not universal defaults.

## Decision Questions

1. Which user journey and device/network profile is affected, and what current field/lab baseline or product objective defines acceptable rendering and interaction behavior?
2. Does the choice change main-thread work, rendering breadth, async race/cancellation behavior, retained listeners/subscriptions/timers, or memory across navigation?
3. How does it change request count, waterfall/fan-out, payload growth, caching/staleness, asset delivery, or offline behavior at the actual route and data scale?
4. Which local state, existing component, platform API, caching layer, worker, memoization, or split point is the smallest evidence-backed option, and what measured constraint rejects the alternative?
5. If bundle, experience, network, and maintainability costs require a broader tradeoff decision, identify `solution-optimality-evaluation` as owner without assuming automatic loading.
