# Inclusive Interaction Contracts

Use this reference to select shared semantic, input, presentation, and verification obligations. Load platform-specific API documentation through the applicable Domain Skill.

Official pages in this reference were recorded as accessed on 2026-07-24.

## Decision Families

| Family | Facts to establish | Acceptance signal |
|---|---|---|
| Semantics | Purpose, role, name, state, value, relationship, and change | Accessibility representation matches visible meaning and interaction |
| Keyboard | Entry, exit, tab sequence, composite keys, activation, escape, and shortcuts | Every outcome is reachable without pointer input |
| Focus | Initial target, visible indicator, modal containment, return, removal, and restoration | Focus remains perceivable and follows the continuing task |
| Announcements | Loading, completion, errors, validation, updated values, and urgency | Material changes are conveyed once without unexpected focus movement |
| Visual meaning | Text contrast, non-text contrast, non-color cues, high contrast, and themes | Information remains distinguishable under supported presentation settings |
| Adaptation | Zoom, text scale, reflow, localization, orientation, and reduced motion | Content and actions remain complete without clipping or forced animation |
| Direct manipulation | Touch target, precision need, drag, swipe, pointer, and motion input | An equivalent non-drag or non-precision action reaches the same outcome |
| Forms | Labels, instructions, required state, field association, error summary, and preserved input | The user can locate, understand, correct, and resubmit invalid input |
| Proof | Static rules, semantic tree, contrast, keyboard, assistive technology, and user evaluation | Evidence names tools, versions, journeys, findings, and unverified scope |

## Source-Derived Constraints

- WCAG 2.2 defines web-content success criteria for names, focus, contrast, color, motion, target size, dragging alternatives, status messages, errors, and reflow.
- WAI-ARIA Authoring Practices supplies informative keyboard conventions and examples; it is not a normative conformance standard or a UI design system.
- W3C states that evaluation tools can assist but no tool alone determines whether a site meets accessibility standards.
- W3C mobile guidance applies existing accessibility standards to mobile contexts but does not create a separate final mobile conformance standard.
- Windows guidance independently requires keyboard, automation-tree, display-setting, and manual assistive-technology checks for Windows applications.

## Primary Sources

- [Web Content Accessibility Guidelines 2.2](https://www.w3.org/TR/WCAG22/)
- [WAI-ARIA Authoring Practices Guide introduction](https://www.w3.org/WAI/ARIA/apg/about/introduction/)
- [WAI keyboard interface practice](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)
- [W3C evaluating web accessibility](https://www.w3.org/WAI/test-evaluate/)
- [W3C mobile accessibility](https://www.w3.org/WAI/standards-guidelines/mobile/)
- [Microsoft Windows accessibility overview](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-overview)
- [Microsoft Windows accessibility testing](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-testing)

## Version And Inference Limits

WCAG 2.2 is a W3C Recommendation for web content. APG is informative guidance. W3C's WCAG 2.2 mobile application guidance was still described as in progress when accessed.

Microsoft pages are rolling Windows guidance. None of these sources establishes the repository's required conformance level, jurisdiction, supported assistive technologies, platform API, or product policy.

Do not infer native-client certification from WCAG alone. Do not infer usability from an accessibility tree, automated scan, numerical contrast result, or one assistive-technology run.

## Required Record

Return applicable requirement authority, semantic and input decisions, focus and announcement behavior, presentation alternatives, form recovery, automated evidence, manual journeys, assistive technologies and versions, unresolved findings, and explicit proof limits.
