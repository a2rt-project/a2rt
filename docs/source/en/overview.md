# Protocol overview

The architecture uses shared time and capacity to organize information that belongs together, while allowing independent synchronization groups to progress separately. Deployments may use networks, local communication, or embodied systems. Configuration must match actual production, processing, transport, and consumption capacity.

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

Canvas selects six domain tracks plus the unique system input track, synchronized delivery, one active task per actor, and asynchronous recording. Other Profiles may choose different tracks and domain rules. See [Canvas adaptation](profiles/canvas.md).
