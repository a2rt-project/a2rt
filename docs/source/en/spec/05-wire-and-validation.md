# Wire format and validation

The [Chinese draft]({{ base }}docs/zh/spec/05-wire-and-validation.html) and downloadable schemas define the detailed fields.

## Common envelope

Every message has `protocol="a2rt/0.2"`, `kind`, `sender`, `session_id`, non-negative integer `epoch`, `manifest_id`, `message_id`, and `sent_at={clock_id,t_us}`.

| Kind | Additional fields |
| --- | --- |
| `output` | `output_seq` starting at 1, `observed_feedback_seq`, one `event`, `updates` |
| `feedback` | `feedback_seq` starting at 0, `reply_to`, `updates` |
| `media` | `updates` on `assistant.audio` only |
| `control` | `request_id`, `action`, `target`, `reason` |

A non-null `reply_to` requires a result for that output's event. It can reference the same output multiple times for progress. Initial observations and batch receipts may use null; each result still identifies its event.

An output may have empty updates. Media cannot hide events. Feedback carries only environment tracks. Unknown fields are rejected outside declared extension areas.

## Formats

Core formats cover audio, observed event records, execution results, playback progress, control results, and visuals. Profile state formats wrap a declared schema ID, revision, and domain value.

`assistant.events` registers `core.event`, carried only in `output.event`. Playback positions are exclusive sample endpoints. A stopped playback does not erase already-presented audio.

## Validation boundaries

Schema checks alone do not prove compatibility. Validate manifest hashes, Profile payloads, registered sources and clocks, sample ranges, causal references, windows, operation state, and dependencies.

```sh
python protocol/validate_examples.py
```

The documentation validator checks metadata and key counterexamples. It does not play media, execute actions, run actual recovery timers, or certify production interoperability. See [examples](../examples.md) for downloads and fixture coverage.
