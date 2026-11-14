# Core, capabilities, and Profiles

This chapter is an English guide to the [Chinese draft]({{ base }}docs/zh/spec/01-core-and-profiles.html).

## Layers

| Layer | Responsibility |
| --- | --- |
| Core | Messages, tracks, identity references, clocks, operation boundaries, receipts, recovery |
| Environment Profile | Domain events, state schemas, tools, execution policies, concurrency, dependencies |
| Adapter | Real execution and observation in an application or device |
| Binding | Reliable delivery, authentication, media resources, flow control |

Core does not define canvas object IDs, selections, viewports, or application versions.

## Manifest and identity

The manifest is negotiated before F0. It registers Profiles with versions and SHA-256 hashes, trusted sources and actors, streams and clocks, domain schemas, tools, limits, and each context's selected execution policy. It is immutable within an epoch.

`sender=assistant/environment` expresses direction. Actor and source identity are separate. A binding must associate authenticated principals with permitted sources, contexts, and capabilities; a string in a model-generated message is not authorization.

## Event

An Event contains `event_id`, `actor_id`, `context_id`, `time`, `operation_id`, `phase`, `type`, `payload`, and `timing`. Retransmission preserves both ID and content.

`assistant.events` requests execution through `output.event`. An environment event is `{event, disposition: "observed"}`: a fact that must not be executed again. Its timing is `immediate`, with the actual source timestamp.

Core reserves `core.noop` and `core.tool_call`. A no-op has an empty payload, null operation ID, and phase `none`. A tool call preserves its server binding, original name, and arguments, with phase `begin`. Other types are registered by Profiles; `core.*` is reserved.

Validate the core envelope and the negotiated domain schema, then check permissions, dependencies, and actual state.

## Operations and tools

`begin → update* → end/cancel` describes one continuous operation; `single` describes a single-event operation. Ending an operation requires actual completion and cleanup. Cancellation does not automatically undo prior effects.

Profiles define `max_active_operations` and `operation_scope`. They may allow one or multiple operations. Tool calls can use MCP adapters, but a transport's request ID alone does not provide side-effect deduplication.
