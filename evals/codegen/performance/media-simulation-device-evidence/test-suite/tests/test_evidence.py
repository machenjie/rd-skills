import copy
import importlib.util
import os
import unittest
from fractions import Fraction
from pathlib import Path


def subject():
    path = Path(os.environ["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"]) / "subject.py"
    spec = importlib.util.spec_from_file_location("candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def media():
    point = lambda value: [value, 1, 90000]
    frames = [{"id": name, "pts": point(pts), "dts": point(dts), "keyframe": name == "I"}
              for name, pts, dts in (("I", 0, 0), ("P", 6000, 3000), ("B", 3000, 6000))]
    record = {"frames": frames, "tracks": ["audio", "video"], "coverage_end": point(9000),
              "playback": [{"kind": "present", "frame": name, "clock": point(pts), "audio_pts": [audio, 1, 48000]}
                           for name, pts, audio in (("I", 0, 0), ("B", 3000, 1600), ("P", 6000, 3200))],
              "seek": {"target": point(3000), "decoded": ["I", "P", "B"], "presented": ["B", "P"]},
              "track_events": [("start", "audio"), ("start", "video"), ("stop", "audio"), ("stop", "video")], "terminal": "eof"}
    policy = {"required_tracks": ["audio", "video"], "required_end": point(9000), "av_tolerance": [1, 1, 1000],
              "max_lateness": [20, 1, 1000], "stale_policy": "drop", "seek_tolerance": [1, 1, 1000]}
    return record, policy


def simulation():
    record = {"frames": [{"render_ms": delta, "paused": paused, "steps_ms": steps}
                         for delta, paused, steps in ((10, False, [10]), (50, False, [10,10]), (500, True, []), (0, False, [10,10]), (5, False, [10]))],
              "save": {"version": 1, "counter": 9}, "loaded": {"version": 2, "score": 9},
              "events": [{"id": "a", "tick": 1, "delta": 4}, {"id": "a", "tick": 1, "delta": 4}, {"id": "b", "tick": 3, "delta": -1}],
              "effects": ["a", "b"], "final_score": 12, "environment": "fixture-cpu-v1", "seed": 7,
              "replay": {"environment": "fixture-cpu-v1", "seed": 7, "effects": ["a", "b"], "final_score": 12}}
    return record, {"step_ms": 10, "catchup_cap": 2, "backlog_policy": "retain"}


def device():
    required = {"shader": "shader-v1", "asset": "asset-v1", "layout": "stride16", "interface": "vec4->vec4", "options": ["precise"]}
    pipeline = dict(required, epoch=1)
    record = {"initial_epoch": 1, "events": [
        {"kind": "submit", "epoch": 1, "resource": "buffer", "fence": "f1", "pipeline": pipeline},
        {"kind": "signal", "epoch": 1, "fence": "f1"},
        {"kind": "wait-complete", "epoch": 1, "fence": "f1"},
        {"kind": "visible", "epoch": 1, "fence": "f1"},
        {"kind": "host-read", "epoch": 1, "resource": "buffer", "after": "f1"}]}
    return record, required


class EvidenceAssertions(unittest.TestCase):
    def test_media_uses_presentation_time_and_exact_timebases(self):
        record, policy = media()
        result = subject().media_evidence(record, policy)
        self.assertEqual(result["failures"], set())
        self.assertEqual(result["pts"]["B"], Fraction(1, 30))
        self.assertEqual(result["dts"]["B"], Fraction(1, 15))
        self.assertEqual(result["presented"], ["I", "B", "P"])
        offset = 2 ** 53 + 1
        for frame in record["frames"]:
            frame["pts"][0] += offset
            frame["dts"][0] += offset
        for event in record["playback"]:
            event["clock"][0] += offset
            event["audio_pts"] = list(event["clock"])
        record["seek"]["target"][0] += offset
        result = subject().media_evidence(record, policy)
        self.assertEqual(result["failures"], set())
        self.assertEqual(result["pts"]["I"], Fraction(offset, 90000))

    def test_media_policy_boundaries_and_stale_drop_are_supplied(self):
        record, policy = media()
        record["playback"][1]["audio_pts"] = [103, 1, 3000]
        record["playback"][1]["clock"] = [160, 1, 3000]
        self.assertEqual(subject().media_evidence(record, policy)["failures"], set())
        record["playback"][1]["audio_pts"] = [104, 1, 3000]
        record["playback"][1]["clock"] = [161, 1, 3000]
        self.assertEqual(subject().media_evidence(record, policy)["failures"], {"av-sync", "stale-present"})
        record["playback"][1]["kind"] = "drop"
        self.assertEqual(subject().media_evidence(record, policy)["failures"], set())
        record, policy = media()
        record["playback"][1]["clock"] = [100, 1, 1000]
        policy["stale_policy"] = "keep"
        self.assertEqual(subject().media_evidence(record, policy)["failures"], set())

    def test_media_startup_seek_integrity_and_cleanup_are_separate(self):
        record, policy = media()
        record.update(upload_exit=0, connected=True, playback=[], seek={})
        self.assertEqual(subject().media_evidence(record, policy)["failures"], {"no-playback", "seek-evidence"})
        record, policy = media()
        record["seek"]["presented"] = ["I", "B"]
        self.assertIn("seek-evidence", subject().media_evidence(record, policy)["failures"])
        record, policy = media()
        record["seek"]["decoded"] = ["B"]
        self.assertIn("seek-evidence", subject().media_evidence(record, policy)["failures"])
        record, policy = media()
        record["tracks"] = ["video"]
        record["coverage_end"] = [1, 1, 1000]
        record["track_events"].pop()
        for terminal in ("eof", "cancel", "error"):
            record["terminal"] = terminal
            self.assertEqual(subject().media_evidence(record, policy)["failures"], {"media-missing", "media-incomplete", "track-cleanup"})
        record["terminal"] = "open"
        self.assertNotIn("track-cleanup", subject().media_evidence(record, policy)["failures"])

    def test_fixed_steps_pause_catchup_and_time_conservation(self):
        record, policy = simulation()
        result = subject().simulation_evidence(record, policy)
        self.assertEqual(result["failures"], set())
        self.assertEqual(result["steps"], [1,2,0,2,1])
        self.assertEqual(result["active_ms"], 65)
        self.assertEqual(result["backlog_ms"], 5)
        self.assertEqual(sum(result["steps"]) * 10 + result["backlog_ms"] + result["discarded_ms"], 65)
        policy["backlog_policy"] = "discard"
        record["frames"][3]["steps_ms"] = []
        record["frames"][4]["steps_ms"] = []
        result = subject().simulation_evidence(record, policy)
        self.assertEqual(result["failures"], set())
        self.assertEqual(result["steps"], [1,2,0,0,0])
        self.assertEqual((result["backlog_ms"], result["discarded_ms"]), (5,30))
        record, policy = simulation()
        record["frames"][1]["steps_ms"] = [50,50]
        self.assertIn("simulation-step", subject().simulation_evidence(record, policy)["failures"])

    def test_replay_identity_save_migration_and_environment_scope(self):
        record, policy = simulation()
        result = subject().simulation_evidence(record, policy)
        self.assertEqual((result["effects"], result["score"]), (["a", "b"], 12))
        self.assertEqual(result["determinism"], "within-declared-scope")
        for field, value in (("environment", "other-cpu"), ("seed", 8)):
            changed = copy.deepcopy(record)
            changed["replay"][field] = value
            self.assertEqual(subject().simulation_evidence(changed, policy)["determinism"], "out-of-scope")
        changed = copy.deepcopy(record); changed["effects"] = ["a", "a", "b"]; changed["final_score"] = 16
        self.assertIn("event-effects", subject().simulation_evidence(changed, policy)["failures"])
        changed = copy.deepcopy(record); changed["events"][1]["delta"] = 5
        self.assertIn("event-identity", subject().simulation_evidence(changed, policy)["failures"])
        changed = copy.deepcopy(record); changed["events"] = list(reversed(changed["events"]))
        self.assertIn("event-order", subject().simulation_evidence(changed, policy)["failures"])
        changed = copy.deepcopy(record); changed["loaded"]["score"] = 0
        self.assertIn("save-migration", subject().simulation_evidence(changed, policy)["failures"])
        changed = copy.deepcopy(record); changed["save"]["version"] = 3
        self.assertIn("save-version", subject().simulation_evidence(changed, policy)["failures"])
        changed = copy.deepcopy(record); changed["replay"]["effects"] = ["b", "a"]
        self.assertIn("replay-diverged", subject().simulation_evidence(changed, policy)["failures"])

    def test_device_requires_completion_wait_and_visibility(self):
        record, identity = device()
        self.assertEqual(subject().device_evidence(record, identity)["failures"], set())
        submitted_only = dict(record, events=[record["events"][0], record["events"][-1]])
        self.assertEqual(subject().device_evidence(submitted_only, identity)["failures"], {"fence-completion", "host-visibility"})
        no_wait = dict(record, events=[event for event in record["events"] if event["kind"] != "wait-complete"])
        self.assertEqual(subject().device_evidence(no_wait, identity)["failures"], {"fence-completion"})
        no_visibility = copy.deepcopy(record)
        no_visibility["events"].pop(3)
        self.assertEqual(subject().device_evidence(no_visibility, identity)["failures"], {"host-visibility"})
        no_visibility["events"][-1]["kind"] = "host-reuse"
        self.assertEqual(subject().device_evidence(no_visibility, identity)["failures"], set())
        second = copy.deepcopy(record["events"][0]); second["fence"] = "f2"
        record["events"].append(second)
        self.assertIn("device-dependency", subject().device_evidence(record, identity)["failures"])
        second["depends_on"] = ["f1"]
        self.assertEqual(subject().device_evidence(record, identity)["failures"], set())

    def test_device_loss_invalidates_old_epoch_and_fences(self):
        record, identity = device()
        record["events"].insert(1, {"kind": "lost"})
        result = subject().device_evidence(record, identity)
        self.assertEqual(result["epoch"], 2)
        self.assertIn("device-epoch", result["failures"])
        record, identity = device()
        for event in record["events"]:
            event["epoch"] = 2
            if "pipeline" in event:
                event["pipeline"]["epoch"] = 2
        record["events"].insert(0, {"kind": "lost"})
        self.assertEqual(subject().device_evidence(record, identity)["failures"], set())
        record["events"][1]["pipeline"]["epoch"] = 1
        self.assertIn("device-epoch", subject().device_evidence(record, identity)["failures"])

    def test_hot_reload_cache_identity_includes_every_material_input(self):
        for key, value in (("shader", "shader-v2"), ("asset", "asset-v2"), ("layout", "stride32"), ("options", ["fast"])):
            with self.subTest(key=key):
                record, identity = device()
                changed = copy.deepcopy(identity); changed[key] = value
                record["events"].insert(0, {"kind": "reload", "required": changed})
                self.assertEqual(subject().device_evidence(record, identity)["failures"], {"artifact-identity"})
                record["events"][1]["pipeline"][key] = value
                self.assertEqual(subject().device_evidence(record, identity)["failures"], set())
