# Accessibility Representation, Input, and Scaling

Load this Reference only when Android Views or Compose changes representation,
TalkBack, Switch Access, Voice Access, keyboard or D-pad input, accessibility
focus, interaction alternatives, font or display scaling, or Android-specific
accessibility evidence.

Do not load it when Android behavior is unchanged or the task only names an
Android accessibility API.

Required by `analysis-agent`, `task-agent`, and `review-agent`.

Return `decision-record`, `proof-limit`, and `validation-plan`.

## Decision Rules

- Reuse `accessibility-inclusive-design` for shared semantic, focus, alternative, scaling, and evidence rules.
- Inspect the effective Views or Compose representation consumed by accessibility services and tests.
- Preserve one complete meaning, state, role, action, and traversal unit when Compose merges descendants.
- Treat `clearAndSetSemantics` as replacement of descendant meaning for accessibility, autofill, and test consumers.
- Preserve separate keyboard, D-pad, accessibility-focus, and service-action paths when the changed control supports them.
- Specify explicit focus order only when Android defaults do not match the visible and task order.
- Provide an equivalent action when a gesture, drag, timed input, or pointer path is not operable through the required service or input device.
- Validate layouts at the supported maximum font and display scaling instead of extrapolating from default density.
- Do not derive nonlinear font dimensions from one scalar when the supported Android behavior is nonlinear.
- Apply the Foundation focus-restoration and one-time-announcement rules across configuration recreation, process-death restoration, and navigation return; restore focus to a still-valid continuing-task target, and suppress stale asynchronous completions and repeated effects.
- Bind pane and live-region behavior to that lifecycle rule so recreation, restoration, or navigation return neither loses the continuing accessibility-focus target nor repeats an announcement.

## Failure Proof

- Inspect merged and unmerged Compose semantics when merging or clearing changes.
- Exercise changed flows with TalkBack or Switch Access when that service is in scope.
- Exercise Tab and directional traversal when keyboard or D-pad input is in scope.
- Exercise the supported maximum font and display scaling with clipping, overlap, reachability, and state changes.
- Across configuration recreation, process-death restoration, and navigation return:
  - Prove that an invalid prior accessibility-focus target falls back to a still-valid continuing-task target.
  - Prove that stale asynchronous completions and repeated effects do not emit the pane or live-region announcement twice.
- Combine automated checks with manual service evidence.
- Record unavailable devices, services, OS versions, and user evidence as proof limits.

## Primary Sources

- [Principles for improving app accessibility](https://developer.android.com/guide/topics/ui/accessibility/principles)
- [Compose semantics](https://developer.android.com/develop/ui/compose/accessibility/semantics)
- [Merging and clearing Compose semantics](https://developer.android.com/develop/ui/compose/accessibility/merging-clearing)
- [Support keyboard navigation](https://developer.android.com/develop/ui/views/touch-and-input/keyboard-input/navigation)
- [Android 14 nonlinear font scaling](https://developer.android.com/about/versions/14/features#accessibility)
- [Compose accessibility testing](https://developer.android.com/develop/ui/compose/accessibility/testing)

## Source Limits

These pages do not prove repository framework versions, the effective runtime
tree, custom-control behavior, supported devices, actual service output, or
complete user testing.
