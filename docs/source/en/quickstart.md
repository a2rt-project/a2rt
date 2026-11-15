# Integration design steps

Start with architecture configuration and a Profile contract. There is no matching new SDK, wire schema, or runtime yet; these are design steps, not instructions for launching a production session.

## 1. Identify participants and capacity

Identify the agent endpoint, environment endpoint, trusted coordinator, publishers, and receivers. Define an operating range using capture, encoding, transport, decoding, and processing capacity. Record transport receipt, model consumption, and user presentation as distinct facts.

## 2. Design the clock tree

Configure the unique root origin, `frequency_hz`, `standard_frame_bytes`, and `standard_frames_per_tick`. Child periods are positive integers in parent ticks; offsets are nonnegative integers. Check exact integer-root-tick mapping along the tree without rounding.

A 1,000 Hz root with a child period of 100 root ticks yields a 10 Hz child. This does not require a message at every root tick or guarantee 1 ms end-to-end latency.

## 3. Define synchronization groups

Choose `sync_group_id`, `clock_id`, and `start_tick` for content that shares a window. Put Profile delivery rules in `delivery_policy`, and whole-group encoded capacity plus per-receiver queue limits in `limits`. Check shared root capacity across overlapping windows, bursts, and sustained demand.

## 4. Register tracks and formats

Each track references one group and one format, and declares its role, direction, and allowed publishers. The format catalog uses `media_type + constraints`. JSON uses an inline `schema` or `schema_ref`, never both; a Profile may allow generic JSON without either. Confirm compatible capabilities before freezing the epoch configuration.

Exactly one system input track is required. If both sides must publish separate data frames in the same period, use two ordinary unidirectional tracks. The system track cannot be duplicated.

## 5. Specify Profile responsibilities

Define presentation mapping, timeout recovery, completeness, and content validation, including responsible implementations. Specify system/assistant events and schemas and any output/task boundaries. The coordinator performs interruption, closure, and cleanup without waiting for notification delivery.

## 6. Validate design and implementation separately

Explore the [complete configuration](examples.md). Check tree structure, references, integer mapping, single-frame slots, and shared budgets. Implementation validation also needs media handling, fragmentation, queues, late data, conflicts, recovery, and real latency. Documentation checks are not runtime conformance certification.
