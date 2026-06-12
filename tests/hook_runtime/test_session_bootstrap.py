from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
BOOTSTRAP_SCRIPT = SCRIPT_DIR / "changeforge_session_bootstrap.py"


def run_bootstrap(
    event: dict,
    cwd: Path,
    cache: Path,
    *,
    mode: str | None = None,
    agent: str | None = None,
) -> subprocess.CompletedProcess[str]:
    event = dict(event)
    event["cwd"] = str(cwd)
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(cache)
    if mode is None:
        env.pop("CHANGEFORGE_HOOK_MODE", None)
    else:
        env["CHANGEFORGE_HOOK_MODE"] = mode
    if agent is None:
        env.pop("CHANGEFORGE_AGENT", None)
    else:
        env["CHANGEFORGE_AGENT"] = agent
    return subprocess.run(
        [sys.executable, str(BOOTSTRAP_SCRIPT)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )


class SessionBootstrapTests(unittest.TestCase):
    def test_session_start_warn_emits_route_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "repo"
            cache = Path(tmp) / "cache"
            cwd.mkdir()
            event = {"hookEventName": "SessionStart"}
            result = run_bootstrap(event, cwd, cache, mode="warn", agent="claude")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(
                payload["hookSpecificOutput"]["hookEventName"], "SessionStart"
            )
            context = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("route preflight", context.casefold())
            self.assertIn("change-forge-router", context)
            # Advisory only: it must never emit a block decision.
            self.assertNotIn("\"decision\"", result.stdout)

    def test_codex_session_start_uses_additional_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "repo"
            cache = Path(tmp) / "cache"
            cwd.mkdir()
            event = {"hook_event_name": "SessionStart"}
            result = run_bootstrap(event, cwd, cache, mode="warn", agent="codex")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(
                payload["hookSpecificOutput"]["hookEventName"], "SessionStart"
            )
            self.assertIn(
                "route preflight",
                payload["hookSpecificOutput"]["additionalContext"].casefold(),
            )

    def test_off_mode_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "repo"
            cache = Path(tmp) / "cache"
            cwd.mkdir()
            event = {"hookEventName": "SessionStart"}
            result = run_bootstrap(event, cwd, cache, mode="off", agent="claude")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_monitor_mode_emits_no_reminder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "repo"
            cache = Path(tmp) / "cache"
            cwd.mkdir()
            event = {"hookEventName": "SessionStart"}
            result = run_bootstrap(event, cwd, cache, mode="monitor", agent="claude")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_non_session_start_event_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "repo"
            cache = Path(tmp) / "cache"
            cwd.mkdir()
            event = {"hookEventName": "Stop"}
            result = run_bootstrap(event, cwd, cache, mode="warn", agent="claude")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_empty_event_fails_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "repo"
            cache = Path(tmp) / "cache"
            cwd.mkdir()
            result = subprocess.run(
                [sys.executable, str(BOOTSTRAP_SCRIPT)],
                input="",
                text=True,
                capture_output=True,
                cwd=str(cwd),
                env={**os.environ, "XDG_CACHE_HOME": str(cache), "CHANGEFORGE_AGENT": "claude"},
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
