# Root clocks, synchronization groups, and tracks

**Architecture design draft · 2026-11-16.** This guide follows the current Chinese specification. Examples describe design relationships; the Canvas local mock implements only part of the design, not a generally released wire schema or complete runtime.

## Four layers

A2RT organizes information through a standard root clock, child clocks, synchronization groups, and configurable tracks. Role and direction belong only to tracks. A clock provides rhythm and coordinate conversion; a group provides the relationship between tracks sharing a window. Sharing a clock, frequency, or ancestor does not create a cross-group waiting barrier.

<img src="{{ base }}assets/clock-groups.svg" alt="Clock tree, groups, and tracks">

Every group binds exactly one clock. A clock can serve multiple independent groups. Every track references one group through `sync_group_id`, inheriting its clock rather than declaring another logical clock. A group may bind root directly.

## The standard root clock

Each configuration epoch has exactly one root with the reserved, case-sensitive ID `root`. It has no parent. Child clocks cannot reuse this ID; duplicate IDs, multiple roots, missing parents, cycles, or nodes that do not reach root are invalid.

| Attribute | Meaning |
| --- | --- |
| `clock_id` | Exactly `root` |
| `frequency_hz` | Positive root frequency; not an audio sample rate or video frame rate |
| `origin` | Common origin for root tick zero; device mappings belong to the Binding |
| `standard_frame_bytes` | Positive integer bytes per standard logical capacity unit |
| `size_scope` | `a2rt_frame`: serialized A2RT headers, metadata, fragmentation information, and payload; excludes underlying transport headers |
| `standard_frames_per_tick` | Positive integer capacity units per root tick |

Frequency, unit size, and units per tick jointly define a scheduling contract. They must reflect sustainable production, encoding, transport, decoding, processing, and consumption capacity. A single-packet delay is only one possible measurement, not a root-clock definition. Deployments may use networks, local transport, shared memory, or embodied systems.

Runtime and Binding implementations must enforce the selected pacing, fragmentation, in-flight volume, and queue limits. Continually filling an unbounded socket buffer does not satisfy the contract. Sustained queue growth or deadline misses require investigating configuration and enforcement. Valid arithmetic alone does not establish a latency guarantee. Conditions outside the agreed operating range are handled by Profile/Binding exception and recovery rules.

## Three frame concepts and one slot per track

A **standard frame unit** measures byte capacity. A **track data frame** is one logical submission by a track in a period. A **group information frame** collects data frames from distinct tracks in one group window and may occupy multiple capacity units.

Within a session, `(epoch, sync_group_id, frame_seq)` identifies the group information frame. Every member data frame has its own `track_id`, which must reference a track belonging to that group. One frame-level track ID cannot stand for every member.

**Each track has at most one data frame per period of its synchronization group.** The unique position is `(epoch, sync_group_id, frame_seq, track_id)`. It refers to the original window, not the period when a message happens to arrive. Zero frames are possible; a submitted empty or held frame occupies the slot. New content needs a later period. Lateness does not change identity or source time.

All sources and both directions share the same slot. A Profile cannot wrap multiple independent same-track frames in an array or batch to evade this constraint. A payload may contain samples or business fields under its declared content contract, but cannot redefine frame boundaries to bypass the limit.

Fragments and identical original-frame retries remain one logical frame and are reassembled/deduplicated. Different content or a different publisher at an occupied position is a conflict, not a replacement. Retries must not replay actions or consume audio twice. Actual reassembly and integrity checking belong to the Binding.

## Child clocks and exact integer alignment

A child declares `clock_id`, `parent_clock_id`, positive integer `period_parent_ticks`, and nonnegative integer `offset_parent_ticks`. It inherits the standard frame unit and does not separately declare frequency or unit size.

```text
child frequency = parent frequency / period_parent_ticks
parent tick = offset_parent_ticks + child tick × period_parent_ticks

P_root = 1; O_root = 0
P_child = P_parent × period_parent_ticks
O_child = O_parent + P_parent × offset_parent_ticks
child tick k maps to root tick O_child + k × P_child
```

Every integer clock boundary and both ends of every group window must map **exactly to integer root ticks**. `P_c` is a positive integer and `O_c` a nonnegative integer. These are derived quantities, not extra configuration fields. Nonzero integer offsets are allowed; all origins need not coincide.

Profiles and Bindings cannot relax this rule using rounding or skew tolerance. A future rational representation must still preserve exact integer-root alignment. Incompatible desired boundaries require a finer compatible root and a newly negotiated epoch, not reinterpretation of existing frames.

## Groups: identity, delivery policy, and limits

| Configuration | Attributes and responsibility |
| --- | --- |
| Core group identity | Unique `sync_group_id`, one `clock_id`, nonnegative `start_tick` (default zero) |
| `delivery_policy` | Profile rules such as `max_wait_root_ticks`, `max_skew_root_ticks`, and `on_timeout` |
| `limits` | `max_frame_units` for the entire encoded group frame and `receiver_queues` for each receiver |

A group has no role, direction, independent frequency, or independent unit size. Tracks declare membership; the group does not repeat a member list. Delivery policies use root-tick units, but the Profile defines the waiting origin, compared timestamps, and actions. Example names such as `suspend` and `deliver_partial` are not a closed Core enumeration. Policies may be specified in versioned documentation rather than encoded entirely as JSON.

`limits.max_frame_units` is a positive integer bound on the whole group's member frames plus A2RT overhead, with both directions combined. Each applicable receiver has one `receiver_queues` entry with a known, nonduplicated `receiver_id` and positive `max_pending_frames`. The agent and environment may have different queues. Missing limits cannot mean unlimited buffering. Fragmentation does not multiply logical queue entries. Excess requires backpressure or an agreed recovery path.

Child clocks do not create capacity. A window spanning K root periods shares K × `standard_frames_per_tick` units with other groups. Group limits do not duplicate this allocation. Check overlapping windows, bursts, sustained demand, and actual resource mappings. Unused capacity does not authorize unlimited bursts.

## Windows and delivery

For zero-based frame sequence n, a group's half-open window is:

```text
[start_tick + n, start_tick + n + 1) in the bound clock
[O_c + (start_tick + n) × P_c,
 O_c + (start_tick + n + 1) × P_c) in root ticks
```

For a 1,000 Hz root and a 10 Hz child with zero offset, windows start `[0,100)`, `[100,200)` ms. An offset of three root ticks makes them `[3,103)`, `[103,203)` ms. `start_tick=0` starts at the bound clock's origin, not necessarily root zero.

The Profile defines sample coverage, event boundary conventions, snapshot cutoffs, valid empty/held content, and version consistency. The Profile also defines what skew tolerance compares; it cannot legalize fractional root boundaries. Common sequence numbers alone do not prove content completeness.

Directions are relative to the designated agent endpoint. The agent receives input tracks and environment-published bidirectional content. The environment receives output tracks and agent-published bidirectional content. Each receiver waits only for applicable members and the agreed publisher for that period. Neither waits for its own output or opposite-direction content.

Both directions can share a group without a circular barrier. A bidirectional track still permits only one data frame per period; use two ordinary unidirectional tracks if both sides must publish separate frames in that period. Profiles/Bindings arrange permitted publishers before accepting frames. Requests and results may occupy different windows and retain causal references.

## Tracks, runtime state, and epochs

A track declares `track_id`, `sync_group_id`, `role`, `direction`, `format_id`, `source_binding`, and a Profile-defined `content_policy`. Role, permitted flow, and actual publisher are distinct concepts. Names do not imply semantics; content cannot override trusted identity. Formats are referenced from the shared catalog and cannot be overridden on a track.

Exactly one track has `role=system`, fixed to `direction=input` and trusted environment/coordinator sources. Its ID need not be the literal string `system`. Its group and notification contract are Profile choices. Assistant outputs and optional model ending requests use assistant output tracks. See [system and lifecycle](04-system-track-and-lifecycle.md).

Runtime records include frame sequence/window, completeness and missing members, receiver backlog, contiguous `delivered_through`, and waiting/recovery/closed state. These do not mutate static configuration. Delivery watermarks are not arrival watermarks or proof of consumption. Root time keeps advancing while delivery is suspended. Control and cleanup cannot wait indefinitely behind missing media.

Clocks, group identity, policies, limits, tracks, and selected formats are frozen within an epoch. Changes require negotiation and a new epoch, preserving old coordinate mappings and recorded facts. Recovery does not replace occupied data-frame positions or rewrite a failure into an earlier success.

The [complete configuration example](../examples.md) uses 94 of 100 units per 100 ms across three groups. It illustrates capacity sharing, not burst scheduling or a runtime performance guarantee. Canvas's task limits and synchronized delivery are [Profile choices](../profiles/canvas.md), not consequences of a clock or frame number.

## Information cadence and admission

Information clocks follow actual production and consumption. A 10 Hz interaction organizes 100 ms observations; finer root ticks, polling, fragments, and internal retries do not require a faster model information rate. New recovery observations occupy legal unoccupied periods. Senders prepare and validate aligned information before transmission; receiver ingress checks readiness before exposing content to the model. Intermediate assembly state is not automatically model input.

Rejecting a frame means it cannot be accepted as valid. It does not require a fixed error message. Profiles may silently discard or select notification and recovery mechanisms; Core does not mandate error-control messages or per-frame ACKs. Frame identity, integer time, queue limits, shared budgets, and truthful delivery state still apply. See [responsibilities](03-core-profile-responsibilities.md).
