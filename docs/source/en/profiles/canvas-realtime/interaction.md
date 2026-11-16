# Canvas interaction and delivery

**Profile `0.3.0-draft`.** These choices apply to the Canvas Realtime local mock, not to every A2RT Profile. Read the [implementation scope](index.md#implemented-scope) and [sender/model responsibilities](../../spec/03-core-profile-responsibilities.md).

## Time and publication positions

The epoch has a 1,000 Hz root and a 1,024-byte standard unit. Interaction periods are 100 root ticks, notification periods 10 ticks, both with zero offset. Six business tracks use `canvas_interaction`; system uses `system_notifications`.

At legal acquisition starts:

```text
root_tick = visible_time_ms + 100
frame_seq = root_tick / 100
publication window = [frame_seq × 100, (frame_seq + 1) × 100)
```

Preroll `[0,100)` holds initial scene and empty audio; visible time zero maps to root tick 100. Normal mode lasts 24 seconds. A publication window identifies the frame position, not every medium's coverage: assistant audio covers the next 100 ms; user feedback covers the interval from the previous successfully delivered observation cutoff to the current one.

## Events, tasks, and tools

Events carry `event_id`, `actor_id`, `context_id`, `task_id`, `phase`, `type`, `payload`, `timing`, and `time`. User input facts may carry `disposition=observed`. Ordinary assistant events name the last complete `basis_observation_id`.

| Event | Contract |
| --- | --- |
| `canvas.pointer` | Down/begin, move/update, up/end, cancel/cancel; unpressed move is single |
| `canvas.tool_call` | Synchronous mock tool task with `server_id`, `name`, and Profile-validated arguments |
| `canvas.noop` | Empty payload, null task ID, phase none; may occur while a pointer task waits |
| `canvas.output_end` | Names `output_id`; ends this output, not the whole session |

Only `canvas.output_end` uses the event track's `mode=control` envelope; the others use `mode=data`. This is still ordinary track content with a single period slot, not a Core error-control message or a trackless channel. Transport recovery belongs to runtime, not model events.

Each actor may have one task. Pointer and tool tasks cannot interleave for the same actor, while user and assistant may each act concurrently. Audio and no-ops do not occupy an extra task. END/CANCEL clears pressed state, pointer capture, and task state; a trusted executor can clean up after a lost END. Identical retries of an `event_id` deduplicate; changed content conflicts.

The `canvas-editor` mock tools are `editor_set_tool`, `editor_set_style`, and `editor_action` with alignment/grouping actions. Tool declarations use MCP-style names and `inputSchema`, but this is not an official MCP service or a complete editor tool set. Selection feedback includes element/group IDs, bounds, `selection.revision`, capabilities, and tool state. Selection-dependent assistant actions need a complete valid observation.

## Observation completeness

The model receiver considers the four business inputs; the environment receiver considers the two assistant outputs. System is independent. The model's complete observation requires:

1. Exactly one frame for each of `user.audio`, `user.events`, `environment.visual`, and `environment.state`. User events may be explicitly empty; past events retain their original periods and are referenced by state `user_event_refs`.
2. Matching visual/state revision, scene, and snapshot cutoff. The cutoff is the current publication window's start.
3. User audio continuously covers the interval from the last successfully delivered cutoff to this cutoff, without conflicting overlap. Preroll has no audio; the first valid cutoff is root tick 100. Known silence uses real zero samples; an unknown gap is not silence.
4. Received audio bytes match sample counts and coverage; the frozen visual scene is usable. A real image/video interface would additionally require its declared rendering/encoding and decoding conditions.

The same `ModelIngress` serves simulation and HTTP reception. It assembles packets, deduplicates, verifies audio continuity and scene consistency, and calls `onObservation` only for complete, unexpired observations. Early state can be staged while visual content is in flight; this does not allow a second updated state frame in the same period.

## Audio and action timing

At 24 kHz mono, a 100 ms assistant segment has 2,400 samples and 4,800 L16 bytes. `timing.sample` associates an operation with the first relevant sample; its dependencies execute before that audio plays. An injected illegal tool event is not attached to unrelated narration.

Two observation cutoffs 200 ms apart require 4,800 user samples. Transfer delay does not determine audio duration: a visual arriving 180 ms late keeps its original capture cutoff. Audio headers declare `coverage`, `start_sample`, and `sample_count`; the body contains those samples. After the 24-second simulated source, this mock explicitly generates and transmits zero PCM.

## Timeout, recovery, and suspension

`max_wait_root_ticks=300` starts with the first staged post-action input. `max_skew_root_ticks=0` concerns content cutoff alignment, not identical network arrival times.

| Visible time | Fault-mode behavior |
| --- | --- |
| 4,800 ms | Unit 48 / UI unit 49 captures an observation; visual is delayed 180 ms |
| 4,980 ms | The visual arrives with its original 4,800 ms cutoff |
| 5,000 ms | The next operation occupies a legal new period |
| 14,200 ms | Unit 141 / UI unit 142 produces an observation whose visual is delayed 600 ms |
| 14,500 ms | Timeout expires the original observation and frees its pending queue position; coordinator records the system notification |
| 14,520 ms | Sender-side recovery preparation is ready |
| 14,600 ms | A new legal observation is captured with a new frame sequence/revision and unconsumed audio/event references; the original operation is not executed again |
| 14,700 ms | The next ordinary operation runs |
| 14,800 ms | Late original visual is archived under its original identity and never delivered again |

Fault mode lasts 24,500 ms; normal mode lasts 24,000 ms. Recovery does not require an assistant transport command or an empty assistant recovery-audio frame.

For a persistent visual fault, recovery failure at 14,520 ms suspends model decisions. After 2,000 root ticks the executor immediately clears the task; resulting state is published at the next legal period, 16,600 ms. Without visual data this is not a complete observation. User audio continues at legal 100 ms intervals through the 24-second source.

System events include `session.started`, `observation.timeout`, `observation.recovered`, `session.suspended`, `task.cleaned`, and `session.ended`. These are this Profile's choices, not a Core enumeration. Suspension cannot masquerade as session completion; a discarded observation cannot masquerade as successful consumption.
