# A2RT documentation

**Agent-to-Real-Time Protocol · Architecture design draft · 2026-11-16**

A2RT is a real-time business-information protocol for agents and environments, providing configurable tracks and a shared time contract. A standard root clock supplies time and capacity; child clocks organize update rhythms; synchronization groups define common windows; configurable tracks carry roles, directions, and content.

```{note}
Canvas Realtime provides a 0.3.0-draft Profile, session configuration, schemas, and documentation of a partial local mock. A general wire release and runtime covering all current constraints remain unavailable. Local validation does not establish production readiness or real model integration. This guide follows the current detailed Chinese specification.
```

Senders prepare consumable information and own send-side recovery; receivers validate it. Models do not assemble packets or retry transport. Profiles choose discard, notification, and recovery policies; Core does not mandate error-control messages or per-frame ACKs.

## Start here

Read the [overview](overview.md), then follow the [integration design steps](quickstart.md). Explore [configuration examples](examples.md) for window and capacity arithmetic. See [draft status](changelog.md) for the current implementation scope.

## Four levels of time and information

<img src="{{ base }}assets/clock-groups.svg" alt="Root clock, child clocks, synchronization groups, and tracks">

Sharing a clock does not create a shared waiting barrier. Each receiver applies its Profile's delivery conditions, while independent groups advance separately. Core preserves identities, time, and general state; Profiles define presentation, recovery, completeness, and content validation.

| Goal | Read |
| --- | --- |
| Understand rhythms, budgets, and one frame per track | [Clocks, groups, and tracks](spec/01-clock-sync-group-track-model.md) |
| Negotiate media and JSON contracts | [Media types and negotiation](spec/02-media-types-and-negotiation.md) |
| Separate common mechanisms from domain behavior | [Core and Profile responsibilities](spec/03-core-profile-responsibilities.md) |
| Distinguish notifications and lifecycle boundaries | [System track and lifecycle](spec/04-system-track-and-lifecycle.md) |
| See the choices for a collaborative canvas | [Canvas adaptation](profiles/canvas.md) |
| Inspect 10 Hz interaction, binary audio, and runtime recovery | [Canvas Realtime](profiles/canvas-realtime/index.md) |

```{toctree}
:caption: Get started
:maxdepth: 1
:hidden:

Overview <overview>
Integration guide <quickstart>
```

```{toctree}
:caption: Core architecture
:maxdepth: 1
:hidden:

Clocks, groups & tracks <spec/01-clock-sync-group-track-model>
Media & negotiation <spec/02-media-types-and-negotiation>
Core & Profile <spec/03-core-profile-responsibilities>
System & lifecycle <spec/04-system-track-and-lifecycle>
```

```{toctree}
:caption: Profiles
:maxdepth: 1
:hidden:

Canvas integration <profiles/canvas>
Canvas Realtime <profiles/canvas-realtime/index>
```

```{toctree}
:caption: Reference
:maxdepth: 1
:hidden:

Configuration examples <examples>
Glossary <glossary>
Implementation status <changelog>
```
