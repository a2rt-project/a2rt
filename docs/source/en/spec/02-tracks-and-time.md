# Tracks, updates, and time

This chapter summarizes the [Chinese draft]({{ base }}docs/zh/spec/02-tracks-and-time.html).

## Stream identity

Each stream belongs to one logical track and binds a source, content format, and clock. Its `seq` starts at 1 and increases independently. Equal sequence numbers in different streams do not imply simultaneity.

`assistant.events` exists only as `output.event`, using `output_seq`; it must not be duplicated in `updates`. Omitting a track means no update, not clearing its cache or confirming its state.

## Update modes

| Mode | Meaning |
| --- | --- |
| `new` | New data, consumed once |
| `reuse` | A historical visual or domain-state reference with optional re-verification |
| `empty` | `no_new_data`, `not_ready`, or `unavailable`; preserve caches and media positions |
| `gap` | An explicit missing range, not silence or a successful no-op |

Audio and event streams cannot use `reuse`. An old sound must not be replayed or consumed as new input. A re-verification does not change the original data timestamp.

## State and visuals

Domain state carries `{schema_id, revision, value}`. Visual data includes `source_state_refs` describing the versions it actually depicts. State r12 can arrive before a frame of r11; both remain useful, but are not one snapshot.

A visual may arrive before its referenced state. Deliver it with unresolved references, then resolve the relationship when state arrives. Do not claim verification until the relevant evidence is available.

## Clocks and audio

Time is `{clock_id, t_us}`: integer microseconds from a registered monotonic origin, not Unix time. Different clocks require explicit mappings, validity ranges, and error bounds.

Audio describes `start_sample`, positive `sample_count`, content (`media` or `silence`), and `requires_events`. Its covered interval is half-open. Duration comes from sample count and rate, not network latency. Missing samples require a gap or a new stream.

## Local synchronization

An event uses `immediate` timing or targets an actual playback sample with `late_policy=reject/apply_now`. Related audio identifies required events. Register a valid schedule once both are ready, then apply the event at the playback position; do not create a circular wait for prior completion.

Only the explicit dependency waits. Unrelated capture and feedback continue. Remote tools that cannot control application time must not claim precise audio alignment.
