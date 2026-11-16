# Protocol overview

A2RT is a **real-time business-information protocol for agents and environments**. It provides configurable information tracks and a shared time contract: what to exchange, at what rhythm, what must be synchronized, and when the receiver may consume it. Deployments may use networks, local communication, or embodied systems. Timing and capacity must match actual production, processing, transport, and consumption capabilities.

## Protocol positioning and layers

| Normative layer | Responsibility |
| --- | --- |
| Core | Common identities, tracks, clocks, synchronization groups, format declarations, windows, delivery state, and resource constraints |
| Profile | Application content, events, consumption conditions, completeness, presentation, execution, exception handling, and notification choices |
| Binding | Serialization, envelopes, connections, source binding, transport/reassembly, pacing, and capacity/queue enforcement using underlying transport capabilities |

Senders, receivers, adapters, and runtimes are the participants that implement these responsibilities. They are not another normative layer. A process may implement several layers without combining their contracts. Real-time behavior is expressed through agreed rhythms and delivery conditions; the protocol does not unconditionally guarantee throughput or latency.

## The sender owns information preparation

This principle applies in both directions. An environment sender captures, assembles, aligns, and validates observations before sending them. A model service and its adapter organize output audio, actions, and their time relationships. When the selected Profile uses recovery, the sender owns send-side retransmission or recapture.

Receivers still reassemble, deduplicate, decode, validate, and decide readiness. They discard, quarantine, or notify according to the Profile rather than guessing missing business meaning. The model receives content satisfying its input contract and performs reasoning and business output; it does not assemble packets, repair media alignment, or initiate transport retries.

Consumable information can be a streaming segment or an explicitly permitted partial observation with declared omissions. It need not wait for an entire recording, session, or every synchronization group. Information clocks follow actual production and consumption: 10 Hz interaction means 100 ms information windows, even if internal retry timers are finer.

## Profile-defined exception handling

Core does not mandate error control messages, error codes, per-frame ACKs, retransmission requests, a dedicated error track, or an extra notification channel. A Profile may silently discard or notify through a custom track, a separate channel, or another agreed mechanism; it chooses whether to recover or terminate. A valid business failure result is still valid business information.

Rejecting invalid data means it cannot be accepted as valid; it does not require a fixed error response. Discarding cannot fabricate successful delivery, a current image, or silence. Track notifications retain frame and capacity limits; off-track notifications cannot bypass business delivery or shared resource budgets. The unique system input remains required but is not a mandatory error-reporting channel. See [responsibility boundaries](spec/03-core-profile-responsibilities.md).

## From time to content

| Layer | Responsibility | Relationship |
| --- | --- | --- |
| Standard root clock | Common origin, frequency, standard-frame bytes, units per tick | Exactly one `clock_id=root` per epoch |
| Child clock | Update rhythm through a parent period ratio and offset | One parent; ultimately reaches root |
| Synchronization group | Common windows, delivery policy, group budget, receiver queues | Binds one clock |
| Track | Role, direction, source, format, content policy | Binds one group through `sync_group_id` |

Clocks and groups do not define role or direction. Track names do not replace explicit configuration. Separate groups can share a clock without waiting for one another.

## Three different frame concepts

- A **standard frame unit** measures byte capacity, including A2RT envelope and fragmentation overhead.
- A **track data frame** is one logical submission from a track in a period of its group.
- A **group information frame** collects data frames from distinct tracks for one group window. It can occupy multiple standard units.

Each track may contribute at most one data frame per period. Multiple sources and both directions share that slot. Fragmentation and retransmission do not create new slots; different content cannot overwrite an occupied position. A data frame is not a network packet, an audio sample, or one model generation.

## What synchronization covers

A Profile determines required members for each receiver, completeness, valid empty/held content, and timeout behavior. Core advances delivery using those results. When input and output share a group, each receiver waits only for its applicable members, not opposite-direction data or its own output.

A group does not require every member to be present unconditionally. Separate groups advance independently. Execution feedback may arrive in later windows and retains causal references. A Profile maps content time to presentation time; window coordinates alone are not device playback times.

## System notifications and domain contracts

Every configuration must contain exactly one `role=system`, `direction=input` track from a trusted environment or coordinator. A Profile chooses its group and defines its notification names, fields, and schemas. Model content and optional session-ending requests use assistant output tracks.

Core does not impose universal tool events, no-op events, or generation identifiers. Profiles define those contracts, as well as presentation, recovery, synchronization completeness, and content validation. Configuration is frozen within an epoch; negotiated changes preserve the interpretation of historical data.

## Canvas is an instance

Canvas selects six domain tracks plus the unique system input track, synchronized observations, one active task per actor, and asynchronous recording. [Canvas Realtime](profiles/canvas-realtime/index.md) documents a current local mock with a 10 Hz interaction clock, actual binary audio, and sender-owned recovery. Its Profile version and Binding ID do not announce a Core wire release. Other Profiles may choose different tracks and domain rules.
