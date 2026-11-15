# A2RT documentation

**Agent-to-Real-Time Protocol · Architecture design draft · 2026-11-16**

A2RT defines information carriage and synchronization between agents and real-time environments. A standard root clock supplies time and capacity; child clocks organize update rhythms; synchronization groups define common windows; configurable tracks carry roles, directions, and content.

```{note}
A matching new wire protocol version, complete machine definitions, and runtime have not been released. Configuration examples illustrate the design. Configuration checks do not validate runtime behavior. This English guide covers the current rules; the Chinese specification is the detailed source text.
```

## Start here

Read the [overview](overview.md), then follow the [integration design steps](quickstart.md). Explore [configuration examples](examples.md) for window and capacity arithmetic. See [draft status](changelog.md) for the current implementation scope.

## Four layers of organization

<img src="{{ base }}assets/clock-groups.svg" alt="Root clock, child clocks, synchronization groups, and tracks">

Sharing a clock does not create a shared waiting barrier. Each receiver applies its Profile's delivery conditions, while independent groups advance separately. Core preserves identities, time, and general state; Profiles define presentation, recovery, completeness, and content validation.

| Goal | Read |
| --- | --- |
| Understand rhythms, budgets, and one frame per track | [Clocks, groups, and tracks](spec/01-clock-sync-group-track-model.md) |
| Negotiate media and JSON contracts | [Media types and negotiation](spec/02-media-types-and-negotiation.md) |
| Separate common mechanisms from domain behavior | [Core and Profile responsibilities](spec/03-core-profile-responsibilities.md) |
| Distinguish notifications and lifecycle boundaries | [System track and lifecycle](spec/04-system-track-and-lifecycle.md) |
| See the choices for a collaborative canvas | [Canvas adaptation](profiles/canvas.md) |

```{toctree}
:caption: Get started
:maxdepth: 1
:hidden:

overview
quickstart
```

```{toctree}
:caption: Core architecture guide
:maxdepth: 1
:hidden:

spec/01-clock-sync-group-track-model
spec/02-media-types-and-negotiation
spec/03-core-profile-responsibilities
spec/04-system-track-and-lifecycle
```

```{toctree}
:caption: Application Profile
:maxdepth: 1
:hidden:

profiles/canvas
```

```{toctree}
:caption: Reference
:maxdepth: 1
:hidden:

examples
glossary
changelog
```
