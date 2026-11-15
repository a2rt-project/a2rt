# Configuration examples and design checks

The [Chapter 01 example](spec/01-clock-sync-group-track-model.md) illustrates architecture relationships, not a released production wire message. Download the [complete configuration JSON]({{ base }}assets/architecture-example.json). `example:` references are placeholders; a real integration must supply its Profile's content contracts.

## Calculate windows from the root

The example root runs at 1,000 Hz with 1,024 bytes per standard unit and one unit per root tick. An interaction child period of 100 yields 100 ms windows. With zero offset and `start_tick=0`, the first windows are `[0,100)`, `[100,200)`, and `[200,300)` ms.

With a child offset of three root ticks, they become `[3,103)`, `[103,203)`, and `[203,303)` ms. Origins need not coincide; boundaries must map exactly to integer root ticks.

## Share capacity without duplicating it

| Group | Period in root ticks | Units per window | Units per 100 ms |
| --- | --- | --- | --- |
| interaction | 100 | 64 | 64 |
| tactile | 10 | 2 | 20 |
| system_control | 10 | 1 | 10 |

The groups total `64 + 10 × 2 + 10 × 1 = 94` units against 100 root units. This arithmetic illustrates sharing; actual burst scheduling, envelope overhead, and delivery deadlines still require runtime and Binding validation.

## Content limits and group budgets both apply

A format may allow an image up to 1,000,000 bytes. The interaction group's 64 units of 1,024 bytes cannot carry an image near that size. Format limits and group capacity must both be satisfied; fragmentation cannot bypass either.

## One position per track

`(epoch, sync_group_id, frame_seq, track_id)` locates a data frame. Distinct tracks may each contribute one frame. Both ends of a bidirectional state track share one position. Original-frame retransmission and fragments retain identity and are not delivered twice; conflicting content or sources cannot overwrite the position.

## What repository checks cover

```sh
python scripts/check_protocol_docs.py
python scripts/build.py --preview
python scripts/check_site.py
npm test --prefix worker
```

These checks cover documentation provenance, illustrative configuration structure and arithmetic, bilingual website links, and the current AI index/retrieval behavior. They do not validate an unreleased new runtime. Runtime conformance, content handling, and latency targets require separate validation.
