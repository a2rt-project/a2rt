# Draft status and implementation scope

## 2026-11-16 · Current architecture design draft

The specification has four chapters: clocks and synchronization groups; media types and negotiation; Core/Profile responsibilities; and system/lifecycle boundaries. The Canvas page records application-specific adaptation requirements.

Defined invariants include one root, exact integer-root-tick mapping, at most one data frame per track per period, one mandatory system input, shared capacity and receiver queue limits, and configuration frozen within an epoch.

## Current deliverables

- Chinese specification and Chinese/English guides.
- JSON configurations illustrating architecture relationships.
- Bilingual search and AI retrieval indexes generated from these documents.
- Repository checks for provenance, illustrative configurations, links, and retrieval.

## Implementation and validation still needed

A matching new wire protocol version, complete machine definitions, and runtime have not been released. Placeholder example: resources require real Profile definitions. Implementations must separately validate transport framing, reassembly, scheduling, media handling, content validation, and recovery.

Clock and budget settings must match actual capacity. Valid configuration arithmetic does not prove runtime latency, throughput, or synchronization-error targets.

## Provenance

Chinese Core chapters are generated from protocol/ in this repository. The [source record]({{ base }}protocol/SOURCE.json) identifies the upstream commit and file digests. English guides follow the same architecture; the detailed source specification is Chinese.
