# Quickstart

This walkthrough reads and validates the protocol. It does not start a production runtime.

## Get the repository

Use Python 3.11 or later:

```sh
git clone https://github.com/a2rt-project/a2rt.git
cd a2rt
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python protocol/validate_examples.py
```

On Windows, activate with `.venv\Scripts\Activate.ps1`.

## Read a session

1. `protocol/examples/counter.profile.json` declares domain events, tools, state, and policies.
2. `protocol/examples/session.json` binds sources, streams, clocks, and the selected Profile.
3. `protocol/examples/streaming-session.json` records multiple events in one operation, independent audio, and batch receipts.

Negotiate the manifest first, then deliver initial feedback F0 (`feedback_seq=0`). Messages reference the same session, epoch, and manifest.

## Track two limits

An **in-flight event** has been sent but has not received its first real `core.result`. An **active operation** has reserved a slot and has not reached a confirmed terminal state.

They have separate limits. One operation can contain `begin → update → end`. An `accepted` receipt frees that event's in-flight slot, not the operation slot. Sending `end` does not prove cleanup is finished.

## Define your environment

Describe domain events and payload schemas, state schemas, tools, named execution policies, and dependencies. Then implement real execution and recovery. Renaming the counter fixture does not establish a compatible adapter.

Continue with [Core and Profiles](spec/01-core-and-profiles.md) and [execution and recovery](spec/04-execution-and-recovery.md).
