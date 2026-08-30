# Hookless Architecture

rd-skills is a non-intercepting, host-native control plane for AI engineering
work:

```text
Control Plane Prompt + four Agent Profiles + three Skill layers
```

It uses bounded dispatch, selectively loaded Skills, visible Markdown handoffs,
fresh validation, and independent review. It does not install executable hooks,
an interception bridge, a second sandbox, private runtime evidence, or an
internal task-state engine.

There is one Runtime Skill surface: 1 Control plus 25 Professional top-level
Skills. Foundation and modifier-only Domain knowledge is selected JIT behind a
Professional owner. Runtime composition is distinct from the four Agent
Profiles shown in the architecture line above.

This shape keeps control decisions inspectable and makes host-enforcement limits
explicit. It authors, builds, packages, installs, upgrades, and removes standard
Skill and Profile artifacts; it is not a runtime content corpus or a personal
archive system.

Continue to [AI control boundaries](AI_CONTROL_BOUNDARIES.md) for authority,
permissions, evidence, and host enforcement. Use [Operating
model](OPERATING_MODEL.md) for artifact and state flow, [Subagent
model](SUBAGENT_MODEL.md) for role execution, and
[Installation](INSTALLATION.md) for built-artifact boundaries.
