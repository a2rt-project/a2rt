# Examples and validation

The fixtures use a counter environment, independent of any canvas implementation.

## Downloads

| File | Purpose |
| --- | --- |
| [Session manifest]({{ base }}protocol/examples/session.json) | Capabilities, clocks, sources, and streams |
| [Counter Profile]({{ base }}protocol/examples/counter.profile.json) | Domain events, tools, state, and policies |
| [Streaming session]({{ base }}protocol/examples/streaming-session.json) | Multiple events per operation and batch receipts |
| [Asynchronous session]({{ base }}protocol/examples/async-session.json) | Independent modalities, tool progress, historical references, and control |
| [Message schema]({{ base }}protocol/schemas/message.schema.json) | Messages and TrackUpdate |
| [Event schema]({{ base }}protocol/schemas/event.schema.json) | Event envelope |
| [Manifest schema]({{ base }}protocol/schemas/manifest.schema.json) | Session capabilities |
| [Execution policy schema]({{ base }}protocol/schemas/execution-policy.schema.json) | Profile policies |

## Follow the streaming trace

F0 initializes the session. O1, O2, and O3 begin, update, and end one operation without waiting for individual receipts. M1 delivers independent assistant audio. F1 describes a user event, not an acknowledgement of O1–O3. F2 batches their explicit results. O4 starts a tool operation, then F3 and F4 report acceptance and completion.

Media uses `example:` placeholders, not playable recordings or decodable images. Example sample rates and timestamps are not protocol requirements.

## Run the checks

```sh
python protocol/validate_examples.py
```

Positive cases cover multiple in-flight events, batch receipts, repeated progress, another Profile allowing two operations, and visuals arriving before state. Negative cases cover window overflow, incorrect receipt association, events after end, and early sends under `per_event`.

Passing these checks validates the documented structures and selected causal rules. Real media, clock drift, external side effects, authentication, and recovery require separate implementation tests.
