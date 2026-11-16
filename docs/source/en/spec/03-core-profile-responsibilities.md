# Core, Profile, and Binding responsibilities

**Architecture design draft · 2026-11-16.** A Profile is a reusable application specification, such as a canvas, robot-control, or sensor-acquisition Profile. It can include prose, versioned machine-readable configuration, and content schemas. It is not necessarily a script executed by Core.

## Who does what

| Normative layer | Responsibility |
| --- | --- |
| Core | Common identities, configuration references, clock tree and windows, tracks/directions, frame references and uniqueness, format declarations, delivery state, mandatory system input, and resource budgets |
| Profile | Content events and schemas, consumption conditions, output/task boundaries, the system track's group, presentation, recovery, completeness, content validation, exception handling, notification choices, and domain rules |
| Binding | Transport, source identity binding, connection/configuration exchange, fragmentation/reassembly, integrity, and enforcement of pacing, capacity, and queues |

A Profile defines reusable rules and permitted choices. Session configuration selects versions, parameters, and source bindings. Adding a domain does not require adding its business fields to Core. Rules may live in versioned documentation; complete business state machines need not be serialized into configuration JSON.

Core and content validation may run in one process or share code, but their normative responsibilities remain separate. Transport success is not proof of correct content, successful execution, model consumption, or user presentation.

Senders, receivers, adapters, and runtimes are executing participants, not parallel normative layers. A2RT is a real-time business-information protocol: Core organizes information channels and time, Profile defines meaning and consumption conditions, and Binding maps the contract to communication mechanisms. Forwarding or reassembly alone does not transfer a sender's content-preparation responsibility to the receiver.

## Sender responsibility in both directions

**Whoever sends is responsible for preparing information that the receiver can consume under the Profile.** Before transmission, the sender captures or produces content, slices media, maps time, aligns tracks, assembles information, and performs the required checks. When the Profile selects recovery, send-side retransmission, recapture, and failure handling belong to the sender and its runtime.

The receiver still reassembles, deduplicates, decodes, validates, and checks readiness. It may discard, quarantine, notify, or take another Profile-defined action. It maintains truthful waiting, delivery, and consumption positions rather than guessing or repairing the sender's intended business meaning.

| Direction | Sender | Receiver |
| --- | --- | --- |
| Environment → model | Environment adapter/coordinator prepares aligned observations and owns send-side recovery | Model ingress validates and admits consumable information; the model reasons and produces business output |
| Model → environment | Model service/adapter organizes output audio, actions, timing, and send-side recovery | Environment ingress validates, schedules playback/execution, and reports actual business outcomes |

When the environment sends execution feedback, it again becomes the sender responsible for that feedback. A tool failure such as a missing target can be a valid business result, distinct from transport or validation failure.

## Model consumption boundary

Network arrival is not admission to the model. Intermediate fragments, partially assembled observations, retry logs, and packet diagnostics do not automatically become model input. The model does not assemble packets, repair audio/visual alignment, or issue transport retries. Runtime and adapters fulfill those duties under the selected Profile.

Readiness depends on the confirmed model interface. Encoded media or a streaming segment may already be a valid input; decoding everything to raw data is not universally required. A Profile may explicitly permit partial observations with missing-content semantics. There is no universal barrier requiring an entire recording, session, or all synchronization groups to finish.

Information clocks express actual production and consumption rhythms. A 10 Hz interaction contract organizes information every 100 ms. Finer root ticks, fragment scheduling, polling, or a 20 ms retry timer do not require a higher model information rate. New recovery observations enter a legal new period; they cannot overwrite an occupied track slot. Budget real recovery and notification work as well as ordinary traffic.

## Default business channel and exception handling

The normal path carries information prepared and checked by its sender. That is a responsibility contract, not a guarantee that faults never happen or permission to skip receiver validation.

**Core does not mandate error control messages, error codes, per-frame ACKs, retransmission requests, dedicated error tracks, or a separate notification channel.** A Profile may silently discard invalid information, notify using a custom or existing track, use an out-of-track channel, or choose another agreed mechanism. It defines whether to recover, pause, or terminate. Binding implements the choice and may reuse underlying transport reliability without introducing another mandatory acknowledgement layer.

“Reject” means invalid information cannot be accepted as valid; it does not require sending a fixed error response. A missing or discarded frame must not become successful delivery, valid empty content, silence, or a current image. Retained content preserves its original capture time and state. The Profile defines gaps, dependencies, and how later windows proceed.

If notifications are used, specify their scope, source authority, identities/epochs/targets, formats, timing, notification-failure behavior, and model visibility. Track notifications obey one-frame and budget limits. A system notification must use the unique trusted system input; runtime notices must not masquerade as model-produced assistant content.

Out-of-track notifications do not occupy an A2RT track period and do not automatically inherit track role, direction, or synchronization semantics. Their shared-resource overhead still counts. They cannot bypass business-data delivery rules, source authorization, configuration, or session state. A Profile's chosen notification contract must be implemented, but it is not a universal Core requirement.

## Core invariants remain mandatory

A Profile cannot remove or duplicate the unique system input track, allow a second data frame for the same track/period, or relax exact integer-root-tick mapping. Multiple publishers, directions, batches, fragments, and retries do not create additional logical slots. A Profile cannot overwrite common identities, epoch assignments, source time, or recorded outcomes.

Synchronization-group identity is expressed by `sync_group_id`, `clock_id`, and `start_tick`. Profile choices belong in `delivery_policy`. Confirmed resource bounds belong in `limits`, including whole-frame units and separate receiver queues. Splitting those responsibilities does not make resource limits optional. Runtime watermarks and backlog remain separate from static configuration.

## Four Profile responsibilities

| Concern | Core mechanism | Profile decision |
| --- | --- | --- |
| Presentation | Common coordinates, windows, associations, and reported positions/results | Immediate or buffered presentation, mapping content time to device time, media/action alignment, late-content treatment |
| Recovery | Missing/timeout states, common references, epoch isolation, optional notification carriage | Timer origin, discard/notification choices, repair/skip/partial delivery/retry rules, consumption advancement, pause/end/new-epoch decisions |
| Completeness | Shared windows, receiver membership, buffering and delivery state | Required sources, valid empty/held values, decode readiness, state/image consistency, permission to make decisions |
| Content validation | Media/constraint declarations, selected format references, schema exclusivity, references for locating affected data | Schema dialect/resolution, actual payload checks, business validity, timing, and whether/how to report failures |

Moving a responsibility to a Profile does not permit ignoring a declared contract. The responsible implementation must enforce it and distinguish unknown, unvalidated, failed, and successful states. Forwarding nodes need not repeat business validation and must not claim it has occurred.

## Presentation and recovery preserve facts

A window identifies content; it does not schedule a speaker, screen, or actuator by itself. A Profile maps source time to presentation time and records what actually happened without replacing capture time with playback time.

Timeout does not universally mean discard, replay, pause, or retry. Profiles can define repair, skip, partial delivery, termination, or a new epoch. Original frame sequence and window remain fixed during late delivery or recovery. Batched repair across windows preserves each original position and does not add a second data frame to an occupied slot.

Recovery adds new records; it cannot rewrite an earlier failure into success or treat an old side effect as a new request. Retrying an original frame preserves its identity and content; a newly captured observation belongs to a new legal period. Changing epoch preserves old configuration mappings. Concrete retry scope and stopping conditions are Profile-defined. Discarding or notifying is not itself proof of recovery or consumption.

## Receiver-specific completeness

A group can contain inputs and outputs. Each receiver considers only applicable tracks and agreed sources, avoiding a reciprocal waiting barrier. A Profile may use manifests, source watermarks, or reassembly results to decide readiness; Core does not prescribe a universal window-end event or business event counter.

For Canvas, the Profile may require audio coverage for the window and an image from the appropriate state snapshot. Only its adapter can establish those relationships. Common frame numbers alone do not prove them. Storage forwarding may require complete encoded resources; model consumption may require decoded, usable media. A Profile allowing partial delivery must report that condition explicitly.

## Content and lifecycle contracts

Core checks invalid references, unknown tracks, conflicting frame positions, configuration epochs, and simultaneous `schema`/`schema_ref` fields. The Profile-designated implementation checks actual JSON `type`/`required`/`enum` compliance, image dimensions, audio encodings, and business values. Core need not contain a decoder or a particular JSON Schema library.

System and assistant event names, fields, payload schemas, task identifiers, and model output boundaries belong to Profiles. Core does not require `generation_id`, a universal no-op/tool event, or a common generation state machine. A Profile may use continuous output without discrete generation rounds.

The unique system input track may share a group or use an independent group. Actual interruption, closing, and cleanup do not wait for notification delivery. Notification names do not automatically update Core state: a Profile-aware coordinator executes the operation and maintains actual session state. A field or event name cannot bypass negotiation or epoch isolation.

## What a Profile should specify

Specify versions and supported formats; system/assistant content contracts; notification choices, targets, phases, and failure behavior; output and task boundaries where applicable; presentation time mapping; timeout origins and recovery rules; sender preparation and receiver admission; source/receiver completeness rules; unique-publisher arrangements; group policies and per-receiver limits; validation ownership and failure handling. If using silent discard, define the resulting gap and downstream delivery behavior just as explicitly.

Canvas chooses synchronized delivery and at most one task per actor. These domain choices are documented in [Canvas adaptation](../profiles/canvas.md) and do not become requirements for every A2RT environment.
