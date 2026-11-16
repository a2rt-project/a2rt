# Draft status and implementation scope

## 2026-11-16 · Current architecture design draft

The specification has four chapters: clocks and synchronization groups; media types and negotiation; Core/Profile/Binding responsibilities; and system/lifecycle boundaries. Canvas records adaptation requirements; Canvas Realtime documents the current 0.3.0-draft local mock. The protocol defines sender responsibility in both directions, model admission, and Profile-owned exception and notification choices.

Defined invariants include one root, exact integer-root-tick mapping, at most one data frame per track per period, one mandatory system input, shared capacity and receiver queue limits, and configuration frozen within an epoch.

## Current deliverables

- Chinese specification and Chinese/English guides.
- JSON configurations illustrating architecture relationships.
- [Canvas Realtime](profiles/canvas-realtime/index.md) interaction/binary Binding contracts, Profile/session configuration, and six content/envelope schemas.
- Bilingual search and AI retrieval indexes generated from these documents.
- Repository checks for provenance, illustrative configurations, links, and retrieval.

## Implementation and validation still needed

The Canvas local mock implements part of the current design, including 10 Hz interaction, actual L16 streaming, shared ingress validation, and runtime recovery. A general wire version, complete machine definitions, and runtime covering all current constraints remain unreleased. Real model integration, production reconnect, cross-device clock synchronization, and public-network recovery remain unavailable. This website hosts documentation and machine files, not the local mock application. Placeholder example: resources require real Profile definitions. Implementations must separately validate transport framing, reassembly, scheduling, media handling, content validation, and recovery.

Clock and budget settings must match actual capacity. Valid configuration arithmetic does not prove runtime latency, throughput, or synchronization-error targets.

## Provenance

The Chinese overview, Core chapters, and current Profile documentation are generated from protocol/ in this repository. The [source record]({{ base }}protocol/SOURCE.json) identifies the upstream commit and file digests. English guides follow the same architecture; the detailed source specification is Chinese.
