"""Validate A2RT documentation fixtures; this is not a runtime or media executor."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads((ROOT / path).read_text())


class ProtocolError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise ProtocolError(code)


schemas = [json.loads(p.read_text()) for p in sorted((ROOT / "schemas").glob("*.json"))]
for schema in schemas:
    Draft202012Validator.check_schema(schema)
registry = Registry().with_resources(
    (schema["$id"], Resource.from_contents(schema)) for schema in schemas
)


def validate_schema(value, name):
    try:
        Draft202012Validator(
            {"$ref": "urn:a2rt:0.2:" + name}, registry=registry
        ).validate(value)
    except ValidationError as error:
        raise ProtocolError("SCHEMA: " + error.message[:150]) from error


manifest = read("examples/session.json")
validate_schema(manifest, "manifest")
sources = {s["source_id"]: s for s in manifest["sources"]}
streams = {s["stream_id"]: s for s in manifest["streams"]}
contexts = {c["context_id"]: c for c in manifest["contexts"]}
clocks = {c["clock_id"] for c in manifest["clocks"]}
require(len(sources) == len(manifest["sources"]), "DUPLICATE_SOURCE")
require(len(streams) == len(manifest["streams"]), "DUPLICATE_STREAM")
require(len(contexts) == len(manifest["contexts"]), "DUPLICATE_CONTEXT")
profiles, custom_events, tools, states = {}, {}, {}, {}
for item in manifest["profiles"]:
    path = (ROOT / item["schema_ref"]).resolve()
    require(path.is_relative_to(ROOT), "EXAMPLE_PROFILE_PATH")
    require(hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], "PROFILE_HASH")
    profile = json.loads(path.read_text())
    require((profile["id"], profile["version"]) == (item["id"], item["version"]), "PROFILE_VERSION")
    profiles[item["id"]] = profile
    require(bool(profile.get("execution_policies")), "POLICIES_REQUIRED")
    for policy in profile["execution_policies"].values():
        validate_schema(policy, "execution-policy")
    for definition in profile["event_types"]:
        require(not definition["type"].startswith("core."), "RESERVED_EVENT")
        Draft202012Validator.check_schema(definition["payload_schema"])
        custom_events[definition["type"]] = (item["id"], definition)
    for definition in profile["tools"]:
        Draft202012Validator.check_schema(definition["inputSchema"])
        tools[(definition["server_id"], definition["name"])] = (item["id"], definition)
    for name, definition in profile["state_schemas"].items():
        Draft202012Validator.check_schema(definition)
        states[name] = definition

allowed_formats = {
    "assistant.audio": {"core.audio"}, "assistant.events": {"core.event"},
    "environment.audio": {"core.audio"}, "environment.events": {"core.event_record"},
    "environment.visual": {"core.visual"},
    "environment.state": {"core.result", "core.playback", "core.control_result", *states},
}
for stream in streams.values():
    require(stream["source_id"] in sources and stream["clock_id"] in clocks, "STREAM_BINDING")
    require(stream["format"] in allowed_formats[stream["track"]], "STREAM_FORMAT")
for context in contexts.values():
    require(context["profile_id"] in profiles, "CONTEXT_PROFILE")
require(any(s["track"] == "assistant.events" for s in streams.values()), "EVENT_STREAM_REQUIRED")
require(any(s["format"] == "core.result" for s in streams.values()), "RESULT_STREAM_REQUIRED")
require(any(s["format"] == "core.control_result" for s in streams.values()), "CONTROL_RESULT_STREAM_REQUIRED")


def check_event(event):
    validate_schema(event, "event")
    require(event["context_id"] in contexts, "UNKNOWN_CONTEXT")
    require(event["time"]["clock_id"] in clocks, "UNKNOWN_CLOCK")
    profile_id = contexts[event["context_id"]]["profile_id"]
    event_type = event["type"]
    if event_type == "core.noop":
        return
    if event_type == "core.tool_call":
        payload = event["payload"]
        key = (payload["server_id"], payload["name"])
        require(key in tools, "TOOL_UNAVAILABLE")
        owner, definition = tools[key]
        if event["timing"]["mode"] == "audio":
            require(definition.get("supports_audio_timing"), "TIMING_UNSUPPORTED")
        value, schema = payload["arguments"], definition["inputSchema"]
    else:
        require(event_type in custom_events, "UNKNOWN_EVENT")
        owner, definition = custom_events[event_type]
        require(event["phase"] in definition["phases"], "UNSUPPORTED_PHASE")
        if event["timing"]["mode"] == "audio":
            require(definition.get("supports_audio_timing"), "TIMING_UNSUPPORTED")
        value, schema = event["payload"], definition["payload_schema"]
    require(owner == profile_id, "WRONG_PROFILE")
    require(Draft202012Validator(schema).is_valid(value), "INVALID_ARGUMENTS")


def check_session(messages, session_manifest=None, require_settled=True):
    session_manifest = session_manifest or manifest
    validate_schema(session_manifest, "manifest")
    policies = {}
    for context in session_manifest["contexts"]:
        profile = profiles[context["profile_id"]]
        policy_id = context["execution_policy_id"]
        require(policy_id in profile["execution_policies"], "UNKNOWN_EXECUTION_POLICY")
        policies[context["context_id"]] = profile["execution_policies"][policy_id]
    if any(p["operation_scope"] == "actor" for p in policies.values()):
        require(len({(p["operation_scope"], p["max_active_operations"]) for p in policies.values()}) == 1,
                "INCONSISTENT_ACTOR_SCOPE")
    seen, events, outputs, receipts, histories, revisions = {}, {}, {}, {}, {}, {}
    controls, control_results = {}, {}
    audio_cursors, audio_blocks, active, operations = {}, [], {}, {}
    pending = {}
    feedback_seq, output_seq = -1, 0

    def operation_key(event):
        policy = policies[event["context_id"]]
        return (event["actor_id"], event["context_id"] if policy["operation_scope"] == "actor_context" else None)

    def register_event(event, observed=False):
        check_event(event)
        eid, actor, op = event["event_id"], event["actor_id"], event["operation_id"]
        if eid in events:
            require(events[eid] == event, "EVENT_ID_REUSED")
            return  # Retransmission is not a second action.
        if event["type"] != "core.noop":
            key = operation_key(event)
            slots = active.setdefault(key, set())
            if event["phase"] in {"begin", "single"}:
                require(op not in operations, "OPERATION_ID_REUSED")
                require(len(slots) < policies[event["context_id"]]["max_active_operations"], "OPERATION_LIMIT")
                slots.add(op)
                operations[op] = {"actor": actor, "context": event["context_id"],
                                  "type": event["type"], "closing": event["phase"] == "single"}
            else:
                require(op in slots, "OPERATION_NOT_ACTIVE")
                current = operations[op]
                require((current["actor"], current["context"], current["type"]) ==
                        (actor, event["context_id"], event["type"]), "OPERATION_BINDING")
                require(not current["closing"], "OPERATION_ALREADY_CLOSING")
                if event["phase"] in {"end", "cancel"}:
                    current["closing"] = True
            if observed and event["phase"] in {"single", "end", "cancel"}:
                slots.discard(op)
        events[eid] = event

    for message in messages:
        validate_schema(message, "message")
        for key in ("protocol", "manifest_id", "session_id", "epoch"):
            require(message[key] == session_manifest[key], "SESSION_MISMATCH")
        require(message["sent_at"]["clock_id"] in clocks, "UNKNOWN_CLOCK")
        mid = message["message_id"]
        if mid in seen:
            require(seen[mid] == message, "MESSAGE_ID_REUSED")
            continue
        seen[mid] = message
        kind = message["kind"]
        if kind == "output":
            require(feedback_seq >= 0, "SESSION_NOT_READY")
            require(0 <= message["observed_feedback_seq"] <= feedback_seq, "INVALID_OBSERVATION_WATERMARK")
            require(message["output_seq"] == output_seq + 1, "OUTPUT_SEQUENCE")
            require(message["event"]["actor_id"] == session_manifest["assistant_actor_id"], "ACTOR_BINDING")
            check_event(message["event"])
            event = message["event"]
            window = (event["actor_id"], event["context_id"])
            if event["event_id"] not in events:
                require(sum(key == window for key in pending.values()) < policies[event["context_id"]]["max_inflight_events"],
                        "INFLIGHT_LIMIT")
            register_event(message["event"])
            output_seq = message["output_seq"]
            outputs[mid] = message["event"]["event_id"]
            if event["event_id"] not in receipts:
                pending[event["event_id"]] = window
        elif kind == "feedback":
            require(message["feedback_seq"] == feedback_seq + 1, "FEEDBACK_SEQUENCE")
            feedback_seq = message["feedback_seq"]
            reply = message["reply_to"]
            if feedback_seq == 0:
                require(reply is None and not outputs, "INVALID_F0")
            elif reply is not None:
                require(reply in outputs, "UNKNOWN_REPLY")
                expected = outputs[reply]
                require(any(
                    u["stream_id"] in streams
                    and streams[u["stream_id"]]["format"] == "core.result"
                    and u["mode"] == "new" and u["data"].get("event_id") == expected
                    for u in message["updates"]
                ), "REPLY_WITHOUT_RECEIPT")
        elif kind == "control":
            target = message["target"]
            if message["action"] != "resync":
                require(target is not None and (target["event_id"] or target["operation_id"]), "CONTROL_TARGET")
            old = controls.get(message["request_id"])
            require(old is None or old == message, "CONTROL_ID_REUSED")
            controls[message["request_id"]] = message

        for update in message.get("updates", []):
            sid, mode = update["stream_id"], update["mode"]
            require(sid in streams, "UNKNOWN_STREAM")
            stream = streams[sid]
            require(update["track"] == stream["track"] and update["source_id"] == stream["source_id"], "SOURCE_BINDING")
            require(update["time"]["clock_id"] == stream["clock_id"], "STREAM_CLOCK")
            require((kind in {"output", "media"} and update["track"] == "assistant.audio")
                    or (kind == "feedback" and update["track"].startswith("environment.")), "TRACK_DIRECTION")
            history = histories.setdefault(sid, {})
            require(update["seq"] == len(history) + 1, "STREAM_SEQUENCE")
            fmt = stream["format"]
            if mode == "reuse":
                require(fmt == "core.visual" or fmt in states, "REUSE_NOT_ALLOWED")
                ref = history.get(update["ref_seq"])
                require(ref is not None and ref["mode"] == "new", "INVALID_REUSE")
                if update["verification"]:
                    require(update["verification"]["at"]["clock_id"] in clocks, "UNKNOWN_CLOCK")
                    for ref in update["verification"]["state_refs"]:
                        require(ref["stream_id"] in streams and streams[ref["stream_id"]]["format"] in states, "UNKNOWN_STATE_STREAM")
            elif mode == "gap":
                gap = update["data"]
                require(gap["to"] > gap["from"], "EMPTY_GAP")
                if fmt == "core.audio":
                    require(gap["unit"] == "samples" and gap["from"] == audio_cursors.get(sid, 0), "AUDIO_GAP_RANGE")
                    audio_cursors[sid] = gap["to"]
                else:
                    require(gap["unit"] == "time_us", "GAP_UNIT")
            elif mode == "new":
                data = update["data"]
                validate_schema(data, "data#/$defs/" + (fmt[5:] if fmt.startswith("core.") else "state"))
                if fmt == "core.audio":
                    require(data["start_sample"] == audio_cursors.get(sid, 0), "AUDIO_DISCONTINUITY")
                    audio_cursors[sid] = data["start_sample"] + data["sample_count"]
                    if update["track"] == "environment.audio":
                        require(not data["requires_events"], "ENVIRONMENT_AUDIO_DEPENDENCY")
                    audio_blocks.append((sid, data))
                elif fmt == "core.event_record":
                    require(data["event"]["actor_id"] == sources[stream["source_id"]]["actor_id"], "ACTOR_BINDING")
                    require(data["event"]["timing"]["mode"] == "immediate", "OBSERVED_EVENT_SCHEDULED")
                    register_event(data["event"], observed=True)
                elif fmt == "core.result":
                    eid = data["event_id"]
                    require(eid in events, "UNKNOWN_RESULT_EVENT")
                    event = events[eid]
                    require(data["operation_id"] == event["operation_id"], "RESULT_OPERATION")
                    old = receipts.get(eid)
                    if old and data["revision"] == old["revision"]:
                        require(data == old, "RESULT_REVISION_REUSED")
                    else:
                        require(data["revision"] == (old["revision"] + 1 if old else 1), "RESULT_REVISION")
                        require(not old or old["status"] not in {"completed", "rejected", "failed", "cancelled"}, "TERMINAL_RESULT_CHANGED")
                    if event["type"] == "core.noop":
                        require(data["operation_status"] is None, "NOOP_CLEARS_OPERATION")
                    elif data["operation_status"] in {"completed", "failed", "cancelled"}:
                        active.get(operation_key(event), set()).discard(event["operation_id"])
                    receipts[eid] = data
                    pending.pop(eid, None)
                elif fmt == "core.visual":
                    for ref in data["source_state_refs"]:
                        require(ref["stream_id"] in streams and streams[ref["stream_id"]]["format"] in states, "UNKNOWN_STATE_STREAM")
                elif fmt == "core.control_result":
                    request_id = data["request_id"]
                    require(request_id in controls, "UNKNOWN_CONTROL_REQUEST")
                    old = control_results.get(request_id)
                    if old and data["revision"] == old["revision"]:
                        require(data == old, "CONTROL_REVISION_REUSED")
                    else:
                        require(data["revision"] == (old["revision"] + 1 if old else 1), "CONTROL_REVISION")
                        require(not old or old["status"] not in {"completed", "failed"}, "TERMINAL_CONTROL_CHANGED")
                    control_results[request_id] = data
                elif fmt == "core.playback":
                    require(data["stream_id"] in streams and streams[data["stream_id"]]["format"] == "core.audio", "PLAYBACK_STREAM")
                    require(data["played_sample"] <= data["buffered_until_sample"], "PLAYBACK_CURSOR")
                else:
                    require(data["schema_id"] == fmt, "STATE_SCHEMA")
                    require(Draft202012Validator(states[fmt]).is_valid(data["value"]), "INVALID_DOMAIN_STATE")
                    key = (sid, data["revision"])
                    require(key not in revisions or revisions[key] == data, "STATE_REVISION_REUSED")
                    revisions[key] = data
            history[update["seq"]] = update

    for sid, block in audio_blocks:
        require(all(eid in events for eid in block["requires_events"]), "UNKNOWN_AUDIO_DEPENDENCY")
    for event in events.values():
        timing = event["timing"]
        if timing["mode"] == "audio":
            require(any(sid == timing["stream_id"] and event["event_id"] in block["requires_events"]
                        and block["start_sample"] <= timing["sample"] < block["start_sample"] + block["sample_count"]
                        for sid, block in audio_blocks), "UNBOUND_AUDIO_TIMING")
    if require_settled:
        require(not pending, "UNFINISHED_EXAMPLE")
    return len(seen), len(events)


messages = read("examples/async-session.json")["messages"]
streaming = read("examples/streaming-session.json")["messages"]
count, event_count = check_session(messages)
stream_count, stream_events = check_session(streaming)
# Message retries do not replay audio/actions or release extra window slots.
for fixture in (messages, streaming):
    require(check_session([m for message in fixture for m in (message, deepcopy(message))]) == check_session(fixture), "RETRANSMISSION")


def by_id(items, mid):
    return next(m for m in items if m["message_id"] == mid)


def selected_policy(items, policy_id):
    selected = deepcopy(manifest)
    selected["manifest_id"] = "demo-policy-" + policy_id
    for context in selected["contexts"]:
        context["execution_policy_id"] = policy_id
    changed = deepcopy(items)
    for message in changed:
        message["manifest_id"] = selected["manifest_id"]
    return changed, selected


# One fixture also works with per-event feedback; streaming intentionally does not.
require(check_session(*selected_policy(messages, "stepwise")) == (count, event_count), "STEPWISE")
visual_first = deepcopy(messages)
late_state = by_id(visual_first, "f4")["updates"].pop()
by_id(visual_first, "f7")["updates"].insert(0, late_state)
require(check_session(visual_first) == (count, event_count), "VISUAL_WAITS_FOR_STATE")

# Noop can be emitted before a running tool finishes, without requiring audio.
waiting = deepcopy([by_id(messages, mid) for mid in ("f0", "o2", "f3", "o1", "f2", "f4")])
by_id(waiting, "o2").update(output_seq=1, observed_feedback_seq=0)
by_id(waiting, "f3").update(feedback_seq=1)
by_id(waiting, "f3")["updates"][0]["seq"] = 1
by_id(waiting, "o1").update(output_seq=2, observed_feedback_seq=1)
by_id(waiting, "f2").update(feedback_seq=2)
by_id(waiting, "f2")["updates"][0]["seq"] = 2
by_id(waiting, "f4").update(feedback_seq=3)
by_id(waiting, "o1")["sent_at"]["t_us"] = 46000
by_id(waiting, "o1")["event"]["time"]["t_us"] = 46000
by_id(waiting, "f2")["sent_at"]["t_us"] = 47000
by_id(waiting, "f2")["updates"][0]["time"]["t_us"] = 47000
by_id(waiting, "f2")["updates"][0]["data"]["time"]["t_us"] = 47000
require(check_session(waiting) == (6, 2), "NOOP_DURING_TOOL")

# Same actor: two operations are legal only with the parallel Profile policy.
parallel = deepcopy([by_id(messages, mid) for mid in ("f0", "o2", "o3", "f4", "f7")])
by_id(parallel, "o2").update(output_seq=1, observed_feedback_seq=0)
by_id(parallel, "o3").update(output_seq=2, observed_feedback_seq=0, updates=[])
by_id(parallel, "o3")["event"]["timing"] = {"mode": "immediate"}
for seq, mid, reply in ((1, "f4", "o2"), (2, "f7", "o3")):
    f = by_id(parallel, mid)
    f.update(feedback_seq=seq, reply_to=reply, updates=f["updates"][:1])
    f["updates"][0]["seq"] = seq
    f["updates"][0]["data"]["revision"] = 1
# Keep the synthetic source chronology consistent with the alternative trace.
by_id(parallel, "o3")["sent_at"]["t_us"] = 41000
by_id(parallel, "o3")["event"]["time"]["t_us"] = 41000
require(check_session(*selected_policy(parallel, "parallel")) == (5, 2), "PROFILE_PARALLELISM")

# No feedback for a full window does not block independent media or control.
window = deepcopy(streaming[:2])
for seq in range(2, 9):
    m = deepcopy(by_id(streaming, "so2"))
    m.update(message_id=f"window{seq}", output_seq=seq)
    m["event"]["event_id"] = f"window_event{seq}"
    m["sent_at"]["t_us"] = (seq + 4) * 1000
    m["event"]["time"] = deepcopy(m["sent_at"])
    window.append(m)
media = deepcopy(by_id(streaming, "sm1")); media["sent_at"]["t_us"] = 14000
window.append(media)
control = deepcopy(by_id(messages, "c1"))
control["target"] = {"event_id": "se1", "operation_id": "adjust_1"}
window.append(control)
require(check_session(window, require_settled=False) == (11, 8), "CONTROL_AND_MEDIA_BYPASS_WINDOW")
# Query completion alone does not confirm the original events.
query_reply = deepcopy(by_id(messages, "f10"))
query_reply.update(feedback_seq=1)
window.append(query_reply)
require(check_session(window, require_settled=False) == (12, 8), "QUERY_WITHOUT_EVENT_RECEIPT")


def extra_update(items):
    m = deepcopy(by_id(streaming, "so2"))
    m.update(message_id="extra", output_seq=9)
    m["event"]["event_id"] = "extra_event"
    items.append(m)


def reuse_audio(items):
    u = by_id(items, "m2")["updates"][0]
    u.pop("data")
    u.update(mode="reuse", ref_seq=1, verification=None)


def insert_conflict(items):
    new = deepcopy(by_id(items, "o3"))
    new.update(message_id="conflict", observed_feedback_seq=3, updates=[])
    new["event"]["timing"] = {"mode": "immediate"}
    items.insert(items.index(by_id(items, "f4")), new)


def after_end(items):
    new = deepcopy(by_id(items, "so2"))
    new.update(message_id="after_end", output_seq=4)
    new["event"]["event_id"] = "late_move"
    items.insert(4, new)


def failed_receipt_then_update(items):
    # An admitted but failed operation does not allow its later queued events to run.
    f = deepcopy(by_id(streaming, "sf2"))
    f.update(message_id="early_failure", feedback_seq=1, updates=f["updates"][:1])
    f["updates"][0]["data"].update(status="failed", operation_status="failed", error={"code":"test", "message":"failed"})
    items.insert(2, f)


checks_run = 0

def negative(name, mutate, expected, fixture=None, policy_id=None, require_settled=True):
    global checks_run
    sample = deepcopy(messages if fixture is None else fixture)
    mutate(sample)
    selected = None
    if policy_id:
        sample, selected = selected_policy(sample, policy_id)
    try:
        check_session(sample, selected, require_settled=require_settled)
    except ProtocolError as error:
        require(str(error).startswith(expected), name + ": unexpected error " + str(error))
    else:
        raise ProtocolError(name + ": invalid example accepted")
    checks_run += 1


checks = [
    ("audio reuse", reuse_audio, "REUSE_NOT_ALLOWED"),
    ("unknown event", lambda x: by_id(x, "o3")["event"].update(type="other.unsupported"), "UNKNOWN_EVENT"),
    ("overlapping operations", insert_conflict, "OPERATION_LIMIT"),
    ("missing associated receipt", lambda x: by_id(x, "f2").update(updates=[]), "REPLY_WITHOUT_RECEIPT"),
    ("unknown reply", lambda x: by_id(x, "f4").update(reply_to="unknown_output"), "UNKNOWN_REPLY"),
    ("future observation", lambda x: by_id(x, "o2").update(observed_feedback_seq=99), "INVALID_OBSERVATION_WATERMARK"),
    ("empty with fabricated data", lambda x: by_id(x, "f0")["updates"][1].update(data={}), "SCHEMA"),
    ("unknown image state stream", lambda x: by_id(x, "f5")["updates"][0]["data"]["source_state_refs"][0].update(stream_id="unregistered"), "UNKNOWN_STATE_STREAM"),
    ("audio skipped without gap", lambda x: by_id(x, "f9")["updates"][1]["data"].update(start_sample=1440), "AUDIO_DISCONTINUITY"),
    ("source impersonation", lambda x: by_id(x, "f8")["updates"][0]["data"]["event"].update(actor_id="assistant"), "ACTOR_BINDING"),
    ("changed event identity", lambda x: by_id(x, "o3")["event"].update(event_id="e2"), "EVENT_ID_REUSED"),
    ("invalid tool argument", lambda x: by_id(x, "o2")["event"]["payload"]["arguments"].update(value="five"), "INVALID_ARGUMENTS"),
    ("audio event outside chunk", lambda x: by_id(x, "o3")["event"]["timing"].update(sample=2000), "UNBOUND_AUDIO_TIMING"),
    ("accepted is not completed", lambda x: by_id(x, "f6")["updates"][0]["data"].update(operation_status="completed"), "SCHEMA"),
    ("unmatched control result", lambda x: by_id(x, "f10")["updates"][0]["data"].update(request_id="unknown"), "UNKNOWN_CONTROL_REQUEST"),
    ("legacy gate", lambda x: by_id(x, "o1").update(after_reply="f0"), "SCHEMA"),
    ("sequence gap", lambda x: by_id(x, "o2").update(output_seq=10), "OUTPUT_SEQUENCE"),
]
for name, mutate, expected in checks:
    negative(name, mutate, expected)
negative("stepwise waits", lambda x: None, "INFLIGHT_LIMIT", streaming, "stepwise")
negative("single operation policy", lambda x: None, "OPERATION_LIMIT", parallel)
negative("window full including after query", extra_update, "INFLIGHT_LIMIT", window, require_settled=False)
negative("end closes input", after_end, "OPERATION_ALREADY_CLOSING", streaming)
negative("failed operation continuation", failed_receipt_then_update, "OPERATION_NOT_ACTIVE", streaming)
negative("policy must be declared", lambda x: None, "UNKNOWN_EXECUTION_POLICY", streaming, "missing")

print(f"Passed: {len(schemas)} schemas, pinned profile hash, {len(streams)} streams / 6 logical tracks, "
      f"{count + stream_count} fixture messages, {event_count + stream_events} events, "
      f"Profile scheduling, batching, window/operation limits, independent media/control and {checks_run} negative cases.")
