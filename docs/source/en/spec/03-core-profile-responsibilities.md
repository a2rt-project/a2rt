# Core and Profile responsibilities

**Architecture design draft · 2026-11-16.** A Profile is a reusable application specification, such as a canvas, robot-control, or sensor-acquisition Profile. It can include prose, versioned machine-readable configuration, and content schemas. It is not necessarily a script executed by Core.

## Who does what

| Layer | Responsibility |
| --- | --- |
| Core | Common identities, configuration references, clock tree and windows, tracks/directions, frame references and uniqueness, format declarations, delivery state, mandatory system input, and resource budgets |
| Profile | Content events and schemas, output/task boundaries, the system track's group, presentation, recovery, completeness, content validation, and domain rules |
| Adapter / application | Decode, validate, determine readiness, present, execute, recover, and report actual outcomes under the Profile |
| Binding | Transport, source identity binding, connection/configuration exchange, fragmentation/reassembly, integrity, and enforcement of pacing, capacity, and queues |

A Profile defines reusable rules and permitted choices. Session configuration selects versions, parameters, and source bindings. Adding a domain does not require adding its business fields to Core. Rules may live in versioned documentation; complete business state machines need not be serialized into configuration JSON.

Core and content validation may run in one process or share code, but their normative responsibilities remain separate. Transport success is not proof of correct content, successful execution, model consumption, or user presentation.

## Core invariants remain mandatory

A Profile cannot remove or duplicate the unique system input track, allow a second data frame for the same track/period, or relax exact integer-root-tick mapping. Multiple publishers, directions, batches, fragments, and retries do not create additional logical slots. A Profile cannot overwrite common identities, epoch assignments, source time, or recorded outcomes.

Synchronization-group identity is expressed by `sync_group_id`, `clock_id`, and `start_tick`. Profile choices belong in `delivery_policy`. Confirmed resource bounds belong in `limits`, including whole-frame units and separate receiver queues. Splitting those responsibilities does not make resource limits optional. Runtime watermarks and backlog remain separate from static configuration.

## Four Profile responsibilities

| Concern | Core mechanism | Profile decision |
| --- | --- | --- |
| Presentation | Common coordinates, windows, associations, and reported positions/results | Immediate or buffered presentation, mapping content time to device time, media/action alignment, late-content treatment |
| Recovery | Missing/timeout states, references, system notification carriage, epoch isolation | Timer origin, repair/skip/partial delivery/retry rules, consumption advancement, pause/end/new-epoch decisions |
| Completeness | Shared windows, receiver membership, buffering and delivery state | Required sources, valid empty/held values, decode readiness, state/image consistency, permission to make decisions |
| Content validation | Media/constraint declarations, selected format references, schema exclusivity, error association | Schema dialect/resolution, actual payload checks, business validity, timing, and failure treatment |

Moving a responsibility to a Profile does not permit ignoring a declared contract. The responsible implementation must enforce it and distinguish unknown, unvalidated, failed, and successful states. Forwarding nodes need not repeat business validation and must not claim it has occurred.

## Presentation and recovery preserve facts

A window identifies content; it does not schedule a speaker, screen, or actuator by itself. A Profile maps source time to presentation time and records what actually happened without replacing capture time with playback time.

Timeout does not universally mean discard, replay, pause, or retry. Profiles can define repair, skip, partial delivery, termination, or a new epoch. Original frame sequence and window remain fixed during late delivery or recovery. Batched repair across windows preserves each original position and does not add a second data frame to an occupied slot.

Recovery adds new records; it cannot rewrite an earlier failure into success or treat an old side effect as a new request. Changing epoch preserves old configuration mappings. Concrete retry scope and stopping conditions are Profile-defined.

## Receiver-specific completeness

A group can contain inputs and outputs. Each receiver considers only applicable tracks and agreed sources, avoiding a reciprocal waiting barrier. A Profile may use manifests, source watermarks, or reassembly results to decide readiness; Core does not prescribe a universal window-end event or business event counter.

For Canvas, the Profile may require audio coverage for the window and an image from the appropriate state snapshot. Only its adapter can establish those relationships. Common frame numbers alone do not prove them. Storage forwarding may require complete encoded resources; model consumption may require decoded, usable media. A Profile allowing partial delivery must report that condition explicitly.

## Content and lifecycle contracts

Core checks invalid references, unknown tracks, conflicting frame positions, configuration epochs, and simultaneous `schema`/`schema_ref` fields. The Profile-designated implementation checks actual JSON `type`/`required`/`enum` compliance, image dimensions, audio encodings, and business values. Core need not contain a decoder or a particular JSON Schema library.

System and assistant event names, fields, payload schemas, task identifiers, and model output boundaries belong to Profiles. Core does not require `generation_id`, a universal no-op/tool event, or a common generation state machine. A Profile may use continuous output without discrete generation rounds.

The unique system input track may share a group or use an independent group. Actual interruption, closing, and cleanup do not wait for notification delivery. Notification names do not automatically update Core state: a Profile-aware coordinator executes the operation and maintains actual session state. A field or event name cannot bypass negotiation or epoch isolation.

## What a Profile should specify

Specify versions and supported formats; system/assistant content contracts; notification targets and phases; output and task boundaries where applicable; presentation time mapping; timeout origins and recovery rules; source/receiver completeness rules; unique-publisher arrangements; group policies and per-receiver limits; validation ownership and failure handling.

Canvas chooses synchronized delivery and at most one task per actor. These domain choices are documented in [Canvas adaptation](../profiles/canvas.md) and do not become requirements for every A2RT environment.
