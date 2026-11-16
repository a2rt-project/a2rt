# Canvas Realtime Profile

**Local mock · `canvas.excalidraw.realtime` / `0.3.0-draft` · 2026-11-16.** This instance exercises the current root clock → child clock → synchronization group → track design. `canvas.a2rt.mock.v2` identifies its binary Binding, not a new A2RT Core wire version. Tasks, tools, observation readiness, playback, and recovery are Canvas Profile choices.

The current configuration and schemas are available for inspection:

- [Profile configuration]({{ base }}protocol/profiles/canvas-realtime/profile.json): capabilities, events, tasks, and recovery.
- [Session configuration]({{ base }}protocol/profiles/canvas-realtime/session.json): clocks, groups, formats, and seven protocol tracks.
- [Interaction and delivery](interaction.md): time, feedback, task, and exception contracts.
- [Binary audio Binding](binary-binding.md): actual PCM, HTTP streaming, envelopes, budgets, deduplication, and decoding.

## Six business tracks and one system input

Direction is relative to the model. Only tracks define roles and directions.

| Track | Role | Direction | Content |
| --- | --- | --- | --- |
| `assistant.audio` | assistant | output | L16 bytes, sample coverage, and action dependencies |
| `assistant.events` | assistant | output | Pointer events, tool calls, no-ops, and output end |
| `user.audio` | user | input | L16 bytes sliced to observation cutoffs |
| `user.events` | user | input | Observed user pointer/tool events and executed facts |
| `environment.visual` | environment | input | Frozen scene corresponding to the current canvas image |
| `environment.state` | environment | input | Scene, selection element/group IDs, tool state, results, and playback progress |

All six belong to `canvas_interaction`. The unique `system` track is `role=system`, `direction=input`, published by the trusted coordinator in the independent `system_notifications` group. It appears in the local mock's system/runtime panel and is not a seventh business track. Output end uses assistant events; runtime recovery does not create assistant transport-repair events or additional tracks.

## 10 Hz information, finer scheduling

The root is 1,000 Hz, interaction is **10 Hz / 100 ms**, and notifications are 100 Hz / 10 ms. These two groups deliver independently. A 20 ms internal retry delay does not change the interaction clock or demand a model decision every 10 ms.

Normal mode contains 240 interaction units and a 24-second speech window. The native Excalidraw interface shows collaborator pointers, selection bounds and handles, drawing, dragging, selection, alignment, grouping, erasing, cancellation, and rejected illegal insertions. Each actor has at most one task; user and assistant tasks may run concurrently and audio may overlap them. Local user actions do not wait for the model. Ordinary assistant events require a complete observation.

There are no added object locks. This mock uses deterministic event arrival order; it does not implement the full Excalidraw collaboration conflict algorithm or all editor tools. Fault mode lasts 24.500 seconds: recovery observations and subsequent operations occupy legal 100 ms periods. Late arrival does not change capture time.

## Sender preparation and model admission

The environment sender prepares and validates consistent visual/state snapshots, audio coverage, and events. The model service/adapter is responsible for output organization and send-side recovery in the opposite direction. Receivers still validate and consume or execute qualified content. Reception-side reassembly does not transfer information preparation to the model.

The shared `ModelIngress` incrementally receives packets, checks completeness, deduplicates, quarantines expired observations, and can invoke a readiness callback per window. The HTTP path uses the same ingress. Waiting for the entire recording before arbitrary playback is a diagnostic webpage choice, not a model input requirement.

The environment coordinator's `RecoveryRuntime` recaptures observations in a legal period after timeout. It pauses decisions and cleans up tasks if recovery fails. The assistant waits for a valid observation instead of issuing transport recovery commands.

## Canvas exception choices

This Profile quarantines expired observations and prevents late old visuals from being delivered again. The coordinator publishes its agreed timeout, recovery, and suspension notifications on system. These are Canvas-defined track contents, not mandatory Core error messages. Other Profiles may silently discard or use custom tracks or separate channels; see [responsibility boundaries](../../spec/03-core-profile-responsibilities.md).

## Implemented scope

The source project contains a local inspection/export/replay mock. AI and user behavior are simulated. Server-side TTS WAV files simulate audio sources; actual `audio/L16` bytes are sent in segments over local HTTP and decoded from the receiver's cache. Visual content is an Excalidraw scene rendered by the native engine, not an encoded video stream.

There is no real model connection, microphone capture, business database, or production WebSocket/RTC service. A real vision model interface may need a scene-rendering and image/video-encoding adapter. Deterministic fault tests and local transport tests do not establish production reconnect, cross-device clock synchronization, public-network latency, or production recovery. The website publishes the current contracts and machine files; the local mock application is not hosted here.

```{toctree}
:maxdepth: 1

interaction
binary-binding
```
