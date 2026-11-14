# Asynchronous feedback and execution policies

See the [Chinese draft]({{ base }}docs/zh/spec/03-feedback-loop.html) for the full rules.

## Three independent processes

The environment continuously observes and presents. The model emits events under the selected policy. Ready track data is delivered independently, including standalone assistant audio.

Each model decision produces exactly one Event. A no-action decision uses `core.noop`, but audio streaming and idle periods do not require fabricated no-op heartbeats.

## Policy selection

Each context chooses a Profile's named `execution_policy_id`, frozen within the epoch.

| Field | Meaning |
| --- | --- |
| `feedback_mode` | `per_event` or `windowed` |
| `max_inflight_events` | Events still awaiting their first real receipt |
| `max_active_operations` | Operations not yet confirmed terminal |
| `operation_scope` | `actor` or `actor_context` |

`per_event` requires an in-flight limit of 1. `windowed` permits a bounded number of events without waiting for each previous receipt. Neither mode proves successful execution.

For example, with one operation slot and eight event slots, an agent may send begin/update/end for the same operation. It cannot start a second operation before the first is confirmed terminal. These values are illustrative, not universal defaults.

## Releasing slots

Only an event's first actual `core.result` frees its in-flight slot. Transport ACKs, unrelated feedback, and `reply_to` alone do not. Later receipts update progress without freeing another slot.

`accepted` or `running` does not free an operation slot. A batch receipt lists each event explicitly; there is no implicit cumulative acknowledgement. A failed or cancelled operation must account for queued follow-up events separately.

## Readiness and dependencies

Deliver new audio, state, results, and visuals as they become available. Bounded coalescing is allowed within the negotiated receipt deadline. A slow modality cannot become the global delivery condition.

`observed_feedback_seq` records the feedback watermark actually used for a decision, not a permission token. Per-stream caches retain time and provenance. Dependency barriers govern only the related actions and must not form scheduling cycles.
