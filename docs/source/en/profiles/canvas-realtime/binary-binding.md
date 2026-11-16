# Canvas binary audio Binding

**`canvas.a2rt.mock.v2` · Canvas Profile `0.3.0-draft`.** This local mock uses real audio bytes and JSON application content. Its Binding ID is not a Core wire version.

## Audio format and metadata

The negotiated format is `audio/L16` with `rate=24000`, `channels=1`, and `max_encoded_bytes=131072`. Samples are signed 16-bit two's-complement, big-endian. PCM contains no WAV header, URL, Base64, or JSON sample array. Server-side WAV files are simulated sources: the sender parses RIFF, validates the format, and converts samples to L16.

At 24 kHz mono, 100 ms is 2,400 samples / 4,800 bytes; 180 ms is 4,320 samples / 8,640 bytes. An empty zero-sample frame has no body bytes. Known silence contains actual zero samples.

```json
{
  "track_id": "assistant.audio",
  "source_id": "model",
  "audio": {
    "mode": "data",
    "start_sample": 24000,
    "sample_count": 2400,
    "coverage": {
      "clock_id": "root",
      "start_root_tick": 1100,
      "end_root_tick": 1200
    },
    "requires_events": ["ev_assistant_010"]
  },
  "body": {"offset": 0, "length": 4800}
}
```

This is a header excerpt. `audio` is metadata for the same audio frame, not a JSON media payload or another track. `body` references its bytes in the packet's binary area. Rate and channels come from the negotiated format and cannot be overridden by metadata. [Audio metadata schema]({{ base }}protocol/profiles/canvas-realtime/schemas/audio-metadata.schema.json) checks the header; runtime must separately verify PCM lengths and sample coverage.

Events, visual, state, and system use `application/json` with their own schemas. Visual is a frozen Excalidraw scene, not encoded video.

## A2B2 packet

```text
4 bytes "A2B2"
4 bytes unsigned big-endian JSON header length
UTF-8 JSON header
contiguous L16 bodies
```

JSON tracks use `payload`; audio tracks use `audio` plus `body`, without a JSON audio payload. Body offsets begin at zero and are contiguous, with no padding, overlap, gaps, out-of-bounds ranges, or unclaimed trailing bytes. The packet maximum is 1 MiB; stricter format, group, and root limits still apply.

[Packet schema]({{ base }}protocol/profiles/canvas-realtime/schemas/packet.schema.json) defines the header. Decoded audio is a `Uint8Array`; the inspection UI displays byte counts and a hex summary, not a substitute wire encoding.

Different packets may carry different tracks of the same group window, but each track still has one logical frame. Identical originals deduplicate. Changed metadata, source, or PCM bytes conflict. Encoded capacity includes the outer four-byte stream length, eight-byte packet prefix, UTF-8 header, and actual PCM.

## Local HTTP transport and receiver admission

| Endpoint | Local behavior |
| --- | --- |
| `GET /api/session?mode=normal\|faults\|suspended` | Session and replay index containing text, shapes, sample bounds, and hashes; no embedded audio or WAV URLs |
| `GET /api/stream?mode=normal\|faults\|suspended` | `application/octet-stream`: repeated uint32 big-endian packet lengths followed by A2B2 packets |

The stream is paced at 1× root time, honors HTTP backpressure, and cancels timers on disconnect. Browser `ReadableStream` chunks may split or combine packets. The receiver reconstructs the length-prefixed packets before passing them to the shared `ModelIngress`. `onObservation` admits only complete, valid, unexpired information, never duplicates or incomplete suspended observations.

Playback builds Web Audio buffers from received PCM. There is no fallback WAV URL. The diagnostic webpage receives the full recording before enabling arbitrary replay/seek; this is a review-interface choice, not a requirement to wait for all audio before model consumption.

Receiver failures throw to the local caller/webpage. This does not define a generic remote error-control endpoint. Coordinator timeout/recovery notifications do not prove that an HTTP receive error triggered sender recovery. The Binding does not yet provide a production two-endpoint reconnect/retransmission control service.

User audio continues when a visual fault suspends assistant decisions. An independent collector may receive it without claiming complete visual feedback. Overlapping historical samples must be byte-identical and play once after deduplication. Missing bytes, interruption, or conflicts fail explicitly rather than silently switching to the original source file.

## Capacity, queues, and exports

The session uses 1,024-byte units: 256 units per interaction window, four per notification window, and 256 per root tick. These are local-test settings, not production recommendations. HTTP overhead is outside the A2RT unit while still consuming real transport capacity; wire-byte diagnostics count the full length-prefixed A2B2 stream. Per-receiver pending queues and HTTP backpressure remain enforced.

Recording caches are separate from delivery queues. PCM recording is limited to 60 seconds per actor. Exported `.a2rt` files use `A2R2`, a uint32 JSON-index length, the JSON index, and length-prefixed A2B2 packets, retaining actual bytes rather than Base64.

Content schemas: [events]({{ base }}protocol/profiles/canvas-realtime/schemas/event.schema.json), [visual]({{ base }}protocol/profiles/canvas-realtime/schemas/visual.schema.json), [state]({{ base }}protocol/profiles/canvas-realtime/schemas/state.schema.json), and [system]({{ base }}protocol/profiles/canvas-realtime/schemas/system.schema.json). JSON Schema validation cannot establish PCM correctness or runtime conformance. The source mock separately tests bytes, RIFF conversion, endianness, coverage, deduplication, and local HTTP pacing; those results are not public-network performance guarantees.
