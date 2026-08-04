# Web Document, Event, And Rendering Contracts

Use this reference when a browser change depends on native document semantics, DOM event paths, rendering order, or the accessibility tree.

Official standards and vendor pages in this reference were recorded as accessed on 2026-07-24.

## Decision Matrix

| Boundary | Facts to establish | Decision consequence |
|---|---|---|
| HTML semantics | Content meaning, native behavior, form or navigation role, and supported elements | Prefer the element whose built-in semantics and interaction match the task |
| DOM ownership | Node tree, shadow boundaries, mutation owner, and listener lifetime | Attach behavior at the narrowest stable owner |
| Event dispatch | Capture, target, bubble, composed path, retargeting, cancellation, and default action | Preserve browser behavior unless the product explicitly replaces it |
| Layout | Formatting context, containing block, intrinsic size, overflow, and writing mode | Diagnose geometry before changing paint or compositing hints |
| Paint and stacking | Stacking-context creators, paint order, clipping, transforms, and positioned descendants | Fix the responsible context instead of escalating arbitrary `z-index` values |
| Compositing | Changed pixels, animation properties, layer behavior, memory, and supported engines | Treat promotion as an engine-dependent optimization requiring measurement |
| Accessibility tree | Native semantics, role, name, state, focusability, hidden state, and relationships | Verify the exposed tree and interaction, not DOM shape alone |

## Source-Derived Constraints

- HTML and DOM are Living Standards; their algorithms define semantics and dispatch, but implementation support must still be checked in target engines.
- CSS specifications define formatting, containment, positioning, paint order, and stacking contexts; compositing implementation remains partly engine-dependent.
- ARIA mappings describe how semantics reach accessibility APIs and do not make custom DOM behavior equivalent to native HTML.
- Mozilla's rendering guide describes style, layout, paint, and compositing as diagnostic stages, not guaranteed optimization boundaries across all engines.

## Primary Sources

- [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/)
- [WHATWG DOM Living Standard](https://dom.spec.whatwg.org/)
- [CSS Positioned Layout Level 3](https://www.w3.org/TR/css-position-3/)
- [CSS 2.2 stacking contexts and painting order](https://www.w3.org/TR/CSS22/zindex.html)
- [CSS Containment Level 2](https://www.w3.org/TR/css-contain-2/)
- [Core Accessibility API Mappings 1.2](https://www.w3.org/TR/core-aam-1.2/)
- [Mozilla how browsers work](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work)

## Version And Inference Limits

HTML and DOM are continuously updated Living Standards. CSS Positioned Layout Level 3, CSS Containment Level 2, and Core-AAM 1.2 were current W3C drafts rather than all being final Recommendations when accessed.

Mozilla documentation describes interoperable concepts plus Firefox-informed implementation detail. None of these sources proves the repository's supported browser versions, exact layer promotion, GPU behavior, framework abstraction, or accessibility outcome.

Do not infer that DOM order equals visual, focus, event, or accessibility-tree order. Do not infer that a new stacking context or compositor layer improves performance without target-engine measurement.

## Required Record

Return selected native semantics, DOM and event path, default-action decision, formatting and stacking owners, measured rendering evidence, accessibility-tree result, target browsers and versions, draft dependencies, and explicit non-inferences.
