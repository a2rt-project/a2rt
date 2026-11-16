# System input and lifecycle boundaries

**Architecture design draft · 2026-11-16.** Core requires exactly one system input track per session configuration. Profiles define its notification contract, its group, and the meaning of assistant content.

## Exactly one trusted system input

A system track has `role=system` and fixed `direction=input`, relative to the designated agent endpoint. It is published by a trusted environment or session coordinator. The track ID is registered normally and does not have to be the literal string `system`; uniqueness is counted by role across the entire session configuration, not separately per group, actor, or context.

Zero or multiple system tracks are invalid. A Profile cannot make it optional, duplicate it for different formats, or change it to output/bidirectional. Model content cannot become a trusted system notification by changing its event name. Ordinary environment images, state, and sensor data do not become system events merely because a backend generated them.

Uniqueness applies to the track declaration, not the lifetime notification count. The track can carry notifications across successive periods, while still contributing at most one data frame in each period. Multiple authorized coordinators share that slot and need an agreed publishing arrangement. Empty/missing behavior follows the Profile; lack of notifications does not remove the required track.

## Group choice and delivery

The system track uses the same `media_type + constraints` catalog and track references as other content. JSON schemas are Profile-defined and use either inline or referenced definitions, not both. Core provides no mandatory universal system-event payload schema.

A Profile may put system notifications with media/state for coordinated delivery, or in an independent synchronization group for timely notifications. A separate group is recommended when waiting for media is undesirable, but is not mandatory and need not use a separate physical connection. The track cannot be duplicated merely to reach several groups.

The group's delivery rules belong in `delivery_policy`, and capacity plus receiver queue bounds in `limits`. The system track inherits the same root coordinates and shared budget. Control purpose does not exempt it from the one-frame-per-period rule. New notifications require later periods; fragments and identical original-frame retries preserve identity.

Actual interruption, closure, and cleanup are performed by the coordinator/runtime under the Profile and must not wait for media completion or model understanding of a notification. Notification sent is not proof of processing completed.

The selected Profile, system format, and configuration must be confirmed before receiving system content. Initial connection/configuration exchange and transport ACK do not depend on a fixed notification event name. Core does not require per-frame ACKs. When the Binding uses transport ACKs, they confirm only the transport fact defined by that Binding, not that the model stopped, a task was cleaned up, or the session closed.

## Three distinct ending boundaries

| Boundary | Meaning | Does not prove |
| --- | --- | --- |
| Profile-defined output end | A chosen output unit ends, such as a generation that produces no more content; it can span multiple information frames | Session closed, all audio played, tool done, or pointer task ended |
| Profile-defined task end | An operation reaches its real domain terminal state | Output ended or session closed |
| Session end | The coordinator confirms no new ordinary interaction is accepted | Merely one utterance ended, a tool completed, or data is temporarily absent |

Profiles may use finite generations, continuous streams, or other interaction forms. Core does not require every Profile to have a generation round, task model, `generation_id`, or uniform end event. Common message identity, epoch, and frame references remain distinct from any domain identifiers.

Silence, a completed fragment, transport disconnection, or a task end alone is not session termination. An interrupt notification is not proof the model has already stopped. Once runtime session state is closed, late old output cannot be accepted as new ordinary interaction.

## Assistant requests and coordinator facts

Model content, optional output-ending markers, and requests such as cancel/pause/end use assistant output tracks. The Profile defines whether those requests exist, their identifiers and parameters, how the coordinator decides them, and any reported outcomes. Reporting a model-side outcome does not turn system input into a bidirectional track.

The coordinator interprets the confirmed Profile and updates actual runtime state. Core does not reserve notification names or automatically close, interrupt, or change configuration because of payload strings. A custom notification cannot bypass confirmed configuration and epoch rules. Supporting Core does not imply support for every Profile's system content.

## Illustrative event names

The following names are examples of one hypothetical Profile, not Core standard names, reserved identifiers, or established Canvas interfaces. No ready-to-use schema is implied.

| Hypothetical Profile content | Track | Illustrative meaning |
| --- | --- | --- |
| `session.started` | system input | Coordinator confirmed interaction can begin |
| `session.interrupt` | system input | Interruption was initiated; does not assert completion |
| `session.ended` | system input | Coordinator confirmed session closure |
| `config.activated` | system input | Agreed configuration became active; does not replace negotiation |
| `output.ended` | assistant output | A Profile-defined output unit really ended |
| `session.end_requested` | assistant output | Request closure; acceptance is a coordinator decision |

For an explanation followed by another user question, a Profile may report output end while keeping the session active. For a closure request, the request alone is not the closure fact. For interrupted generation, an adapter may report a real provider terminal result under the Profile; it must not fabricate completion merely because an interrupt was issued, nor require an interrupted model to generate another acknowledgement.

[Canvas Realtime](../profiles/canvas-realtime/index.md) publishes a current versioned contract for its six business tracks and unique system input. Its concrete event catalog is defined by that Profile, not by the illustrative list above.

## Required system input, optional error notification

The system track is required, but it is not a Core-mandated error-reporting channel. A Profile may silently discard or notify through custom tracks, separate channels, or another agreed mechanism. If it selects system for an exception, the trusted coordinator publishes under the system input contract. It cannot add a second system track or make system bidirectional. Off-track notices cannot impersonate system authority or bypass session/configuration constraints.
