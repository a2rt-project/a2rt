# Glossary

| Term | Meaning |
| --- | --- |
| Track | One of six logical categories of information |
| Stream | A named stream bound to a track, source, format, and clock |
| Event | A request or observed fact, depending on direction |
| Operation | A bounded operation with concurrency and cleanup obligations |
| Receipt | An executor's `core.result`, associated by event ID |
| Profile | Domain events, tools, state schemas, and execution policies |
| Manifest | The negotiated capabilities, frozen within an epoch |
| Epoch | A generation of session configuration and identity bindings |
| Actor | A participant, distinct from source device or sender direction |
| Source | A registered origin of data or events |
| Context | An environment context bound to a Profile and policy |
| Binding | Concrete transport, authentication, media, and flow-control rules |
| `observed_feedback_seq` | The feedback watermark used for an output, not a decision permit |
| `reply_to` | Feedback association with an output, possibly repeated for progress |

## Distinctions that matter

`new` adds data. `reuse` references historical visuals or state. `empty` preserves cached content while reporting availability. `gap` marks missing coverage, not silence.

`accepted` is not success. `applied` need not end an operation. `unknown` preserves uncertainty. `cancelled` requires actual termination and cleanup.
