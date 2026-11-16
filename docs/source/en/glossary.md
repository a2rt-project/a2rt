# Glossary

Current architecture design draft · 2026-11-16.

## root

The unique time and capacity baseline per epoch, with ID root.

## Child clock

Derives rhythm from a parent period and offset; inherits units without adding capacity.

## Synchronization group

Binds one clock and organizes tracks by common windows with delivery policy and limits.

## Track

Defines role, direction, sources, and format; references one group through sync_group_id.

## Standard frame unit

A byte-capacity unit including A2RT overhead, distinct from a logical data frame.

## Track data frame

At most one logical submission by a track in one group period.

## Group information frame

A collection of distinct tracks’ data frames in one group period; each references its own track_id.

## frame_seq

Zero-based sequence identifying a fixed window; lateness and retries preserve its identity.

## direction / source_binding

Express content role, flow relative to the agent, and trusted publishers; these are distinct.

## delivery_policy

Profile-defined delivery configuration; timer origins, completeness, and timeout actions need Profile semantics.

## limits

Confirmed group encoding capacity and per-receiver queue limits enforced by Core/Binding.

## constraints / format_id

The type selects constraint rules, constraints declare the contract, and format_id references the session catalog.

## epoch

Scope of frozen configuration; negotiated changes enter a new epoch while history keeps its interpretation.

## system

The mandatory unique input role for system notifications from a trusted environment or coordinator.

## delivered_through

A receiver’s contiguous delivery position, not latest arrival or proof of consumption.

## Profile

Defines domain content, output/task boundaries, presentation, recovery, completeness, and validation.

## Sender responsibility

In both directions, the sender prepares, aligns, and validates consumable information and owns send-side recovery. Receivers still reassemble, deduplicate, decode, and validate without guessing business meaning.

## Model admission

Network arrival does not imply readiness for model consumption. Ingress admits information under the Profile; the model reasons and produces business output rather than assembling packets or retrying transport.

## Exception policy

Profiles choose silent discard, notification, recovery, or termination. Core does not mandate error messages, per-frame ACKs, retransmission requests, or a dedicated error track. Discard cannot fabricate success or completeness.

## Binding

Maps the contract to serialization, envelopes, source binding, transport/reassembly, pacing, capacity, and queue limits. Senders, receivers, adapters, and runtimes are executing participants, distinct from normative layers.

## ModelIngress / RecoveryRuntime

Canvas Realtime local-mock components for ingress validation and environment-side recovery. The former validates packets and quarantines expired observations; the latter recaptures in legal periods. Neither is a model-generated business event.
