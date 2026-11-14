# Versions and draft status

## Draft 0.2 · 2026-11-15

Wire identifier: `a2rt/0.2`.

- Independent track updates, unsolicited environment feedback, and standalone assistant media.
- Removes the 0.1 `after_reply` decision permit; `output_seq` replaces `round_id`.
- `reply_to` only associates requests and may recur for progress.
- Named Profile execution policies, selected by context and frozen within an epoch.
- Separate limits for active operations and events awaiting their first receipt.
- Counter-environment fixtures, schemas, and a documentation validator.

This draft is incompatible with 0.1. Replacing the version string in old recordings is not a migration.

## Further engineering work

Production adapters, transport bindings, media availability and integrity, cross-service idempotency, real clock mappings, packet-loss recovery, dependency-cycle detection, and model consumption of observations all need validation.

The website timeline is an explanatory illustration, not a runtime, benchmark, or interoperability certification.
