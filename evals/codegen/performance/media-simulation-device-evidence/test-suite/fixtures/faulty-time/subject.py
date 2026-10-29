"""Three bounded recorded-evidence validators; no media or device runtime."""
from fractions import Fraction


def _time(point):
    ticks, numerator, denominator = point
    if any(type(value) is not int for value in point) or numerator <= 0 or denominator <= 0:
        raise ValueError("invalid timestamp or timebase")
    return Fraction(float(ticks * numerator) / denominator)


def media_evidence(record, policy):
    failures = set()
    frames = {frame["id"]: frame for frame in record["frames"]}
    pts = {key: _time(frame["pts"]) for key, frame in frames.items()}
    dts = {key: _time(frame["dts"]) for key, frame in frames.items()}
    if not frames or not set(policy["required_tracks"]) <= set(record["tracks"]):
        failures.add("media-missing")
    if _time(record["coverage_end"]) < _time(policy["required_end"]):
        failures.add("media-incomplete")
    if list(dts.values()) != sorted(dts.values()):
        failures.add("decode-order")
    presented = []
    for event in record["playback"]:
        frame = event["frame"]
        if frame not in frames:
            failures.add("media-missing")
            continue
        if event["kind"] == "present":
            presented.append(frame)
            if abs(_time(event["audio_pts"]) - pts[frame]) > _time(policy["av_tolerance"]):
                failures.add("av-sync")
            if policy["stale_policy"] == "drop" and _time(event["clock"]) - pts[frame] > _time(policy["max_lateness"]):
                failures.add("stale-present")
    if not presented:
        failures.add("no-playback")
    seek = record.get("seek", {})
    decoded, shown = seek.get("decoded", []), seek.get("presented", [])
    if not decoded or not shown or any(key not in frames for key in decoded + shown):
        failures.add("seek-evidence")
    else:
        target = _time(seek["target"])
        if (not frames[decoded[0]]["keyframe"] or pts[decoded[0]] > target
                or [dts[key] for key in decoded] != sorted(dts[key] for key in decoded)
                or not set(shown) <= set(decoded) or any(pts[key] < target for key in shown)
                or not target <= pts[shown[0]] <= target + _time(policy["seek_tolerance"])):
            failures.add("seek-evidence")
    active = set()
    for action, track in record["track_events"]:
        if action == "start" and track not in active:
            active.add(track)
        elif action == "stop" and track in active:
            active.remove(track)
        else:
            failures.add("track-cleanup")
    if record["terminal"] in {"eof", "cancel", "error"} and active:
        failures.add("track-cleanup")
    return {"failures": failures, "pts": pts, "dts": dts, "presented": presented}


def simulation_evidence(record, policy):
    step, cap = policy["step_ms"], policy["catchup_cap"]
    if step <= 0 or cap <= 0 or policy["backlog_policy"] not in {"retain", "discard"}:
        raise ValueError("invalid fixed-step policy")
    backlog = discarded = active_time = 0
    counts, failures = [], set()
    for frame in record["frames"]:
        if frame["render_ms"] < 0:
            raise ValueError("negative render delta")
        count = 0
        if not frame["paused"]:
            active_time += frame["render_ms"]
            backlog += frame["render_ms"]
            count = min(backlog // step, cap)
            backlog -= count * step
            if policy["backlog_policy"] == "discard":
                excess = backlog // step * step
                discarded += excess
                backlog -= excess
        counts.append(count)
        if frame["steps_ms"] != [step] * count:
            failures.add("simulation-step")
    saved = record["save"]
    if saved["version"] == 1:
        loaded = {"version": 2, "score": saved["counter"]}
    elif saved["version"] == 2:
        loaded = {"version": 2, "score": saved["score"]}
    else:
        return {"failures": {"save-version"}, "determinism": "unproved"}
    if loaded != record["loaded"]:
        failures.add("save-migration")
    unique, effects, score, last_tick = {}, [], loaded["score"], 0
    for event in record["events"]:
        identity = event["id"]
        value = (event["tick"], event["delta"])
        if identity in unique:
            if unique[identity] != value:
                failures.add("event-identity")
            continue
        unique[identity] = value
        if not last_tick <= event["tick"] <= sum(counts):
            failures.add("event-order")
        last_tick = event["tick"]
        effects.append(identity)
        score += event["delta"]
    if record["effects"] != effects or record["final_score"] != score:
        failures.add("event-effects")
    replay = record["replay"]
    scope = (replay["environment"], replay["seed"]) == (record["environment"], record["seed"])
    determinism = "within-declared-scope" if scope else "out-of-scope"
    if scope and (replay["effects"] != effects or replay["final_score"] != score):
        failures.add("replay-diverged")
        determinism = "diverged"
    return {"failures": failures, "steps": counts, "backlog_ms": backlog,
            "discarded_ms": discarded, "active_ms": active_time,
            "effects": effects, "score": score, "determinism": determinism}


def device_evidence(record, required):
    epoch, identity = record["initial_epoch"], dict(required)
    pending, submitted = {}, {}
    completed, waited, visible, failures = set(), set(), set(), set()
    for event in record["events"]:
        kind = event["kind"]
        if kind == "lost":
            epoch += 1
            pending.clear(); submitted.clear(); completed.clear(); waited.clear(); visible.clear()
            continue
        if kind == "reload":
            identity = dict(event["required"])
            continue
        if event["epoch"] != epoch:
            failures.add("device-epoch")
            continue
        if kind == "submit":
            pipeline = event["pipeline"]
            if pipeline["epoch"] != epoch:
                failures.add("device-epoch")
            if any(pipeline[key] != identity[key] for key in ("shader", "asset", "layout", "interface", "options")):
                failures.add("artifact-identity")
            resource, fence = event["resource"], event["fence"]
            if resource in pending and pending[resource] not in event.get("depends_on", []):
                failures.add("device-dependency")
            pending[resource], submitted[fence] = fence, resource
        elif kind == "signal":
            if event["fence"] not in submitted:
                failures.add("fence-completion")
            else:
                completed.add(event["fence"])
        elif kind in {"wait-complete", "visible"}:
            if event["fence"] not in completed:
                failures.add("fence-completion")
            else:
                (waited if kind == "wait-complete" else visible).add(event["fence"])
        elif kind in {"host-read", "host-reuse"}:
            fence = pending.get(event["resource"])
            if fence is None or event["after"] != fence or fence not in waited:
                failures.add("fence-completion")
            if kind == "host-read" and fence not in visible:
                failures.add("host-visibility")
    return {"failures": failures, "epoch": epoch}
