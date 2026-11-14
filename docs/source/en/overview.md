# Protocol overview

An agent may speak while acting. People may intervene, tools may still be running, and audio and visuals may arrive at different times. A2RT gives these processes common message semantics.

## Six logical tracks

| Track | Content |
| --- | --- |
| `assistant.audio` | Agent audio, explicit silence, and gaps |
| `assistant.events` | Action requests, tool calls, and no-op decisions |
| `environment.audio` | People, other participants, and device audio |
| `environment.events` | Events that have already happened |
| `environment.visual` | Screenshots, frames, or negotiated visual representations |
| `environment.state` | Execution receipts, domain state, control results, playback progress |

Tracks are categories, not six connections. A track may contain multiple named streams. The baseline loop registers `assistant.events` and separate `environment.state` streams for `core.result` and `core.control_result`. Other capabilities are optional.

## Deliver when ready

Feedback may contain only audio, a receipt, or a new frame. A delayed visual keeps its source timestamp and state references. It must not replace a newer confirmed state or masquerade as a current capture.

Synchronization is local: an event explicitly aligned with an audio sample waits for that dependency, without imposing a session-wide barrier.

## Requests and facts

`output.event` requests execution. `core.result` reports actual progress. `accepted` and `running` are not completion. The model cannot certify its own success.

Environment events use the same Event structure but describe observed facts. They must never be executed again.

## Scope

Core defines identity, lifecycle, time, and receipts. Profiles define domain capabilities. Adapters execute them; bindings provide transport and authentication. MCP is one optional tool integration, not a synonym for A2RT.

Draft 0.2 specifies no fixed frame rate, sampling rate, or hard real-time deadline. Implementations must separately validate performance and recovery.
