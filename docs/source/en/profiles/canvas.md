# Canvas Profile adaptation requirements

**Current architecture requirements · 2026-11-16.** This page records Canvas choices without defining a universal Core event enumeration. [Canvas Realtime](canvas-realtime/index.md) supplies a current 0.3.0-draft Profile, session configuration, schemas, and a partial local mock.

## Tracks and groups

Canvas uses six domain tracks plus the mandatory unique system input. Actual track IDs, formats, clock parameters, and schemas require a confirmed versioned configuration.

| Purpose | Role | Direction |
| --- | --- | --- |
| Agent audio | assistant | output |
| Agent operation events | assistant | output |
| User audio | user | input |
| Observed user operations | user | input |
| Canvas images | environment | input |
| Canvas state and execution results | environment | input |
| System notifications | system | input |

`environment` is a Canvas-declared extension role. The six domain tracks may share one interaction group. Agent and environment receivers deliver their own applicable content independently rather than waiting for one another. Canvas selects the unique system track's group and notification contract before integration.

Canvas selects synchronized delivery. Its backend organizes images, state, audio, and events by common windows. The Profile defines snapshot cutoffs, media coverage, valid empty/held values, completeness, and timeout recovery. Recording is asynchronous and is not a real-time delivery readiness condition.

All tracks obey exact integer-root window boundaries and at most one data frame per track per period. Tracks reference `sync_group_id`; policies belong in `delivery_policy`, and capacity/receiver queue limits in `limits`.

## Operations and visible behavior

Each user or assistant actor may run at most one task at a time. The user and assistant may each have a task concurrently, and local user input does not wait for model feedback. Pointer operations express begin, movement, release, or cancellation; a single actor cannot interleave pointer and tool tasks.

Audio can overlap a canvas task. Output end, task end, and session end are distinct. Use native collaborator pointers and selection aids, preserving visible selection bounds, handles, and operations. Feedback state identifies selected elements and groups. Object conflicts use Excalidraw coordination; this Profile introduces no additional object locks.

Canvas defines event names, tool envelopes, parameters, output/task identifiers, and state/result schemas through its media and content contracts. Illustrative events in the generic guide do not become Canvas interfaces.

## Implementation responsibilities

Confirm clocks, groups, tracks, and formats before integration. Implement integer mapping, single-frame positions, shared capacity, and receiver queues. The adapter executes real edits, maps presentation times, checks image/state consistency and observation completeness, and reconciles cancellation, reconnect, and recovery.

System carries trusted input notifications only. Model requests and output boundaries use assistant output tracks. The coordinator performs interruption and cleanup without waiting for notification delivery.

Canvas Realtime uses 10 Hz interaction, native Excalidraw rendering, actual L16 audio over local HTTP, shared ingress validation, and runtime recovery. It does not connect a real model or provide production recovery. Its deterministic mock does not implement the full Excalidraw collaboration conflict algorithm. Configuration arithmetic and documentation checks alone do not validate all current architecture requirements.

## Sender responsibilities and exception choices

The environment sender assembles aligned visual/state snapshots, audio coverage, and event/result associations. Model ingress validates and admits consumable observations. In the other direction, the model service/adapter organizes audio/actions and their time relations; the environment validates, plays, executes, and reports actual results. Each sender owns its send-side recovery. Tool execution failure can be valid business feedback, distinct from transport failure. Models do not repair transport.

Canvas chooses timeout quarantine, runtime recapture, and coordinator notifications. These are Profile choices, not mandatory Core error controls. Late old content cannot replace delivered state, and incomplete observations cannot masquerade as complete feedback. Information cadence follows interaction demand: 10 Hz means 100 ms windows. Finer root ticks and internal retries do not raise the model information rate or permit a second frame in an occupied period.
