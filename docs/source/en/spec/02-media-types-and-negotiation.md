# Media types, formats, and negotiation

**Architecture design draft · 2026-11-16.** Format examples are illustrative. `example:` and `example.org` references require real definitions before integration.

## A common format description

A format has two business fields: `media_type` and `constraints`. `media_type` is a parameter-free `type/subtype` using the IANA media-type system. It selects decoding and the applicable A2RT constraint rules. `constraints` carries configuration and limits for that type. An empty object is allowed only when the selected type's mandatory rules are still satisfied.

Parameters belong in `constraints`, not in a separate parameters object. JSON content schemas use `constraints.schema` or `constraints.schema_ref`. These fields are A2RT configuration, not automatically HTTP header parameters. A Binding maps applicable values to its transport standards without confusing codec, container, or compression semantics.

Constraint names, types, units, defaults, and meanings are fixed by the selected protocol/Profile version. Profiles select supported rules and assign responsibility for validating actual content. Core checks general structure and references; it does not need every media decoder or business validator.

## Format catalog and tracks

The session `formats` catalog stores full descriptions with epoch-local `format_id` values. Tracks reference one catalog item and cannot override its constraints. Multiple tracks can share an item; the same media type with different constraints requires different items. A matching local ID alone does not establish compatibility across sessions.

```json
{
  "format_id": "jpeg_720p_1mb_v1",
  "media_type": "image/jpeg",
  "constraints": {
    "max_width": 1280,
    "max_height": 720,
    "max_encoded_bytes": 1000000
  }
}
```

This limits each image to at most 1280 × 720 pixels and 1,000,000 encoded bytes; smaller images and other aspect ratios are allowed. `width` and `height` instead specify exact dimensions. Exact values and maxima must be mutually satisfiable. One decimal MB is 1,000,000 bytes; one MiB is 1,048,576. Encoded size is distinct from decoded pixel memory.

`audio/L16` means signed 16-bit, big-endian linear PCM. `constraints.rate` is a positive integer exact sample rate; `channels` is a positive integer channel count. The selected configuration must specify rate; omitted channels are normalized to the media default of one before confirmation. Little-endian PCM cannot simply be labelled `audio/L16`. Sample rate, encoded video rate, and group frequency are separate concepts.

## JSON schema choices

| Inline `constraints.schema` | `constraints.schema_ref` | Result |
| --- | --- | --- |
| Present | Absent | Supply the inline content schema to the Profile implementation |
| Absent | Present | Resolve and use the schema under Profile rules |
| Present | Present | Invalid configuration, even if claimed equivalent |
| Absent | Absent | Generic JSON and other declared constraints; a structured domain Profile may require one |

Presence is tested by field existence, not truthiness: `schema: false` is a schema. Inline schemas can be objects or booleans, not null or JSON text strings. A content schema describes decoded JSON payload, not the A2RT envelope or the constraints object.

References bind to immutable content versions and may resolve from a Profile package or preinstalled resource; per-frame network downloads are unnecessary. The Profile specifies reference bases, resolution, schema dialect, optional assertion behavior, validation timing, and failure handling. Draft 2020-12 in examples is not a global Core default. Nested JSON Schema `$ref` remains available under Profile rules.

A forwarding Core need not retrieve or execute a schema. A validator unable to obtain its definition cannot claim validation success. Schema validity does not grant execution permission or establish tool semantics. System and assistant event sets, parameters, output identifiers, and ending markers are Profile contracts; `application/json` does not imply a Core event schema.

## Capability negotiation

A receiver declares a nonempty `accept` list for a track. Each candidate uses the same `media_type` and `constraints` structure, optionally with preference `q`. Constraints belong to individual candidates, not a cross-type top-level object. This phase requires explicit media types; wildcards such as `image/*` are not introduced.

`q` is a preference from zero to one with at most three decimal places, defaults to one, and zero means unacceptable. It is not compression quality and is not a content constraint. Hard compatibility requirements are satisfied before preferences are considered.

1. Core checks candidate structure, references, and schema exclusivity.
2. Profile implementations confirm actual encoding/decoding ability, type-specific constraints, schema support, and content semantics. Unsupported capabilities cannot be advertised as supported.
3. Core/Binding checks common deployment budgets. A Profile cannot silently weaken content limits to obtain a match.
4. JSON compatibility requires an explicitly supported shared contract; matching MIME types is insufficient. No general arbitrary-schema equivalence solver is required. Inline and reference representations can match a confirmed contract, but the final description keeps only one form.
5. The negotiation party chooses among compatible equal-preference items and confirms the complete selected description. It is stored in `formats`, then referenced by the track.
6. No compatible candidate, unmet limits, or unconfirmed selection means failure. A required track failure prevents activating the dependent group configuration.

A bidirectional track initially selects the same format and shared constraints that both ends can encode and decode. Different format needs, or separate same-period publishing, require two ordinary unidirectional tracks. System remains one input track, never duplicated by format or made bidirectional.

Selected formats and constraints are frozen within the epoch. A change requires negotiation and a new epoch. Variable image dimensions can still range within frozen limits; historical data keeps its original interpretation.

## Payload size and fragmentation

`max_encoded_bytes` limits the **complete encoded payload of one track data frame**, not each fragment. A static-image frame carries a complete image; audio carries a contract-defined sample segment; JSON carries one complete value whose structure is defined by the Profile. Multiple fields or samples do not create additional frame slots, and batching cannot hide independent same-track frames in one period.

The count includes representation headers/metadata and UTF-8 JSON bytes. It excludes A2RT envelopes, fragment headers, transport headers, and extra transport Base64 or compression wrappers. A Binding defines how to recover the measured representation. A2RT overhead is still charged to the root capacity budget.

A 1.2 MB image violates a 1 MB limit even when every fragment is smaller. A compliant image may span several standard units while retaining its original frame identity. Multiple image tracks may each contribute one frame, but both per-payload limits and the whole group's `limits.max_frame_units` apply.

## Validation and shared budgets

Image dimensions, audio encoding, content-schema compliance, and business validity are checked by Profile-designated handlers. Core does not treat declared dimensions as proof. Profiles define allowed resizing, quality changes, rejection, recovery, and notifications. Common capacity and reassembly constraints remain mandatory.

At ten images per second, actual 1 MB images alone require 10 MB/s before other tracks and A2RT overhead. The illustrative group's 64 units of 1,024 bytes do not fit a near-1 MB image. Supporting a format maximum does not automatically reserve that capacity; either cover the maximum or define verifiable traffic restrictions.

Received, validated, delivered, consumed, and presented are different facts. Content failures retain their frame/track associations and follow Profile rules. Common time, configuration identity, and history are not rewritten by a format declaration. See [responsibilities](03-core-profile-responsibilities.md) for the full boundary.
