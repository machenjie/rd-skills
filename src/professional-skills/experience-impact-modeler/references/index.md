# Experience Impact Modeler Reference Index

Use this index to load only the local reference needed for the selected experience risk. Record skipped-reference rationale when a plausible reference is not loaded.

| Reference | Load When | Do Not Load When | Depends On | Conflicts With | Professional Depth | Output Fragment |
| --- | --- | --- | --- | --- | --- | --- |
| `../examples/example-output.md` | A compact example helps calibrate flow/state/accessibility handoff wording. | The model needs source-specific validation, screenshots, or analytics proof. | Selected mode, affected flow, and changed state. | Treating example facts as live evidence. | compact | Tiny experience output shape. |
| `references/checklist.md` | A bounded review needs actor, entry, state, accessibility, analytics, and verification inventory. | Full flow evidence, accessibility gates, or experiment proof decides closure. | Screens/routes/components, user roles, states, and validation target. | Checklist completion replacing user-flow evidence. | bounded | Experience checklist. |
| `references/experience-output-and-gates.md` | Closure depends on flow evidence, accessibility/recovery gates, analytics coupling, state-to-validation maps, or handoff fields. | The body output contract is enough and evidence is not being closed. | Flow graph, state matrix, accessibility obligations, commands, reports, screenshots, and proof limits. | Screenshot-only proof for accessibility or recovery. | risk-focused | Output and gate map. |
| `references/journey-risk-patterns.md` | Journey risks involve destructive/sensitive flows, high-volume operational work, experiment instrumentation, stale prior-evidence claims, or proof limits. | A local component UX check has no journey, analytics, or sensitive-flow risk. | User journey, risk mode, stale evidence, instrumentation, owner, and residual risk. | Component-only review hiding end-to-end flow risk. | risk-focused | Journey risk patterns. |
