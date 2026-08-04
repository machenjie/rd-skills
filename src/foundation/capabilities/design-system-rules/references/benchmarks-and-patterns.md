# Design System Rules Benchmarks And Patterns

Load this reference when a shared component, variant, token, interaction, responsive behavior, or accessibility contract is being selected or changed. Do not load it for feature-local layout that neither changes nor challenges the shared system.

## Decision Checklist

1. **Reuse:** inspect current components and compositions; keep behavior feature-local when no shared semantic contract exists.
2. **Variants:** add an axis only for a real product state or interaction distinction, not a screen name or one-off style flag.
3. **Tokens:** use owned color, typography, spacing, radius, elevation, density, and motion tokens, with missing-token ownership recorded instead of embedding a raw value.
4. **Semantics:** choose native elements or an established accessible pattern with correct name, role, value, and state exposed by any custom role.
5. **Keyboard:** define keys, activation, escape/cancel, disabled behavior, and composite-widget navigation from the applicable platform/APG convention.
6. **Focus:** define entry, visible focus, order, trapping when justified, restoration, and focus after async success or failure.
7. **Color:** status, selection, and error meaning must have a non-color cue in every applicable theme.
8. **Contrast:** prove the project’s current accessibility target for text, controls, icons, focus, and themes from policy rather than a remembered threshold.
9. **Motion:** name the purpose, interruption/cancellation behavior, and reduced-motion alternative when animation affects understanding or comfort.
10. **Responsive behavior:** prove primary actions, reading order, overflow, touch/keyboard operation, and data/form behavior at the supported viewports.
11. **Internationalization:** check wrapping, expansion, bidirectionality, number/date formats, and truncation for the supported locale set.
12. **State matrix:** cover applicable default, hover, active, focus, selected, disabled, loading, empty, error, success, and partial states without inventing impossible combinations.
13. **Manual proof:** supplement automation with keyboard, focus, semantic, screen-reader, responsive, color/motion, and content review wherever the tool cannot observe behavior or meaning.
14. **Owner and lifecycle:** name component/API/token owner, current consumers, stories/tests/docs, rollout, migration, deprecation, and the trigger for revisiting a local composition.

## Proof Limits And Routes

Automated scans catch only a subset of accessibility failures; snapshots do not prove interaction, responsive task completion, assistive output, or consumer compatibility. Platform libraries and published ratios are evidence inputs, not substitutes for the repository’s declared target and current component behavior.

Reject speculative shared components, feature vocabulary in shared APIs, arbitrary variant combinations, and raw style values that bypass tokens. Also reject color-only state, invisible focus, automation-only accessibility claims, desktop-only proof, and animation without a current need and reduced-motion behavior.

Route feature/page ownership to `page-component-decomposition`, interaction states to `interaction-state-modeling`, translated/time/money behavior to `i18n-timezone-money-safety`, implementation to `frontend-change-builder`, and executable behavior/accessibility proof to `frontend-testing` or `quality-test-gate`.
