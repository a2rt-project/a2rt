# Execution, recovery, and transport

See the [Chinese draft]({{ base }}docs/zh/spec/04-execution-and-recovery.html) for detailed recovery and cleanup obligations.

## Execution receipts

`core.result` includes `event_id`, `operation_id`, `revision`, `status`, `operation_status`, `time`, `result`, and `error`. Revisions increase per event; duplicate revisions must contain identical facts.

| Status | Meaning |
| --- | --- |
| `accepted` | Validated, deduplicated, and accepted; not necessarily applied |
| `running` | Work is progressing |
| `applied` | This event was applied; the operation may remain active |
| `completed` | The event finished; terminal events also require cleanup |
| `rejected` | Refused before the requested domain effects |
| `failed` | Failed, possibly after partial effects |
| `cancelled` | Actual termination and required cleanup confirmed |
| `unknown` | Actual outcome is not yet known |

`operation_status` is separate. Confirmed terminal operations cannot become active again. `unknown` may converge after reconciliation.

## Deduplication

Deduplicate messages by `message_id`, actions by `event_id`, and media by stream and sample range. Same ID with different content must be rejected. Register effects atomically before execution where required.

A lost in-memory map does not prove exactly-once effects after a crash. External writes need executor-side idempotency or reconciliation. If safe replay cannot be guaranteed, query rather than blindly re-executing.

## Timeout and control

Receipt deadlines concern the first `core.result`, not any feedback or visual frame. On timeout, retain the ledger, mark the outcome unknown, pause ordinary outputs in the affected scope, and recover through `control`.

Controls are `cancel`, `query`, and `resync`, with independent request IDs. `core.control_result` tracks control progress. Completing a query does not prove the original event succeeded or release its slots: the executor must update the event's `core.result`.

Recovery attempts and deadlines are bounded. Unresolved recovery enters `suspended`. Reconnection reconciles or isolates old effects before a new epoch; changing the epoch does not magically stop an external tool.

## Backpressure and recording

Never silently drop receipts, operation boundaries, cancellation, or audio samples. Report gaps and apply stream-specific backpressure. Recording preserves source time and delivery order without blocking the real-time loop. Replay must not send historical actions to a live executor.

The draft assumes reliable, sender-ordered logical delivery. Concrete transports need their own binding, authentication, resource validation, and flow-control rules.
