# A2RT documentation

**Agent-to-Real-Time Protocol · Draft 0.2**

A2RT describes events, media, observations, and execution feedback between an agent and a real-time environment. Each track progresses independently. Ready information is delivered without waiting for every modality, while preserving provenance, time, and causality.

```{note}
The current deliverable is a specification, JSON Schemas, fixtures, and a documentation validator. It is not a production SDK. This English guide summarizes the draft; the Chinese specification and machine-readable schemas provide the detailed rules.
```

## Start here

Read the [overview](overview.md), then [validate a fixture](quickstart.md). Implementers can follow the five Core chapters below. For concrete messages, see [examples and validation](examples.md).

## A continuously running loop

The environment keeps observing. An agent sends events under a Profile's execution policy. An executor reports actual progress. Audio does not need to wait for an action, and a receipt does not need to wait for a visual frame. Explicit local dependencies still apply.

```{toctree}
:caption: Get started
:maxdepth: 1
:hidden:

overview
quickstart
```

```{toctree}
:caption: Core specification guide
:maxdepth: 1
:hidden:

spec/01-core-and-profiles
spec/02-tracks-and-time
spec/03-feedback-loop
spec/04-execution-and-recovery
spec/05-wire-and-validation
```

```{toctree}
:caption: Reference
:maxdepth: 1
:hidden:

examples
glossary
changelog
```
