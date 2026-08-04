#!/usr/bin/env python3
"""Execute and evaluate the Core Principles outcome graph from the Core Model."""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any

from validation_utils import (
    CANONICAL_CORE_PRINCIPLE_IDENTITIES,
    PRINCIPLE_PREDICATE_OPERATORS,
    resolve_json_pointer,
    validate_principle_acceptance_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_CONTRACT_SOURCE = "src/control-model/core-contracts.json"
JSON_REPORT = "reports/core-principles-outcomes.json"
MARKDOWN_REPORT = "reports/core-principles-outcomes.md"
REPORT_SCHEMA_VERSION = 3
MAX_SAVED_REPORT_SCHEMA_ERRORS = 64
MAX_SAVED_REPORT_COLLECTION_ITEMS = 10_000
TIMEOUT_DESCENDANT_DISCOVERY_SECONDS = 0.20
TIMEOUT_TERMINATE_GRACE_SECONDS = 0.25
TIMEOUT_FINAL_WAIT_SECONDS = 0.75
TIMEOUT_TREE_RECHECK_SECONDS = 0.20
TIMEOUT_POLL_SECONDS = 0.02
DARWIN_PROC_ALL_PIDS = 1
DARWIN_PROC_PPID_ONLY = 6
DARWIN_PROC_PIDTBSDINFO = 3
DARWIN_PROC_PIDTBSDINFO_SIZE = 136
DARWIN_PROC_ZOMBIE_STATUS = 5
DARWIN_PID_LIST_ATTEMPTS = 3
DARWIN_PID_LIST_SLACK_BYTES = 4096
PRODUCER_FAILURE_REASON_CODES = {
    "dependency-not-pass",
    "duplicate-argv",
    "process-exit-nonzero",
    "process-start-failed",
    "process-timeout",
    "process-tree-cleanup-failed",
    "report-not-json-object",
    "report-not-refreshed",
    "source-tree-mutated",
}
UNCOVERED_MANDATORY_RELEASE_GATES = [
    "examples-validation",
    "showcase-freshness",
    "marketplace-catalog-freshness",
    "marketplace-index-validation",
    "productization-assets-validation",
    "open-source-readiness",
    "unit-tests",
    "codegen-benchmark-validation",
    "codegen-benchmark-sample-run",
    "quickstart-dry-runs",
    "remote-ci-current-commit",
]
EVIDENCE_LIMITATIONS = [
    "Evidence is limited to static contracts, deterministic fixtures, code-generation definitions and harness or negative-control checks, builds, and simulated installation.",
    "This evaluation does not prove real-host Profile startup, wall-clock performance, production accuracy, or the installed user experience.",
    "The formal Core Principles sub-gate is not the repository formal release gate and does not cover every mandatory release gate listed below.",
]
EXCLUDED_TREE_PREFIXES = (
    ".git/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".venv/",
    "dist/",
    "evals/agent-behavior/outputs/",
    "evals/pressure/outputs/",
    "node_modules/",
    "reports/",
)
EXCLUDED_TREE_PARTS = {"__pycache__"}


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _tree_file_included(relative: str) -> bool:
    if relative == ".DS_Store" or relative.endswith("/.DS_Store"):
        return False
    path = PurePosixPath(relative)
    if any(part in EXCLUDED_TREE_PARTS for part in path.parts):
        return False
    return not any(relative == prefix[:-1] or relative.startswith(prefix) for prefix in EXCLUDED_TREE_PREFIXES)


def input_tree_digest(root: Path) -> dict[str, object]:
    """Digest the input tree while excluding declared generated outputs."""

    digest = hashlib.sha256()
    count = 0
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: _relative(item, root)):
        relative = _relative(path, root)
        if not _tree_file_included(relative):
            continue
        content = path.read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).digest())
        digest.update(b"\0")
        count += 1
    return {"sha256": digest.hexdigest(), "file_count": count}


def _file_snapshot(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"exists": False, "mtime_ns": None, "size": None, "sha256": None}
    stat = path.stat()
    return {
        "exists": True,
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
        "sha256": _sha256_bytes(path.read_bytes()),
    }


def _fresh_report(before: dict[str, object], after: dict[str, object]) -> bool:
    if after["exists"] is not True:
        return False
    if before["exists"] is not True:
        return True
    return (
        before["mtime_ns"] != after["mtime_ns"]
        or before["size"] != after["size"]
        or before["sha256"] != after["sha256"]
    )


def _sha256_stream(stream: Any) -> str:
    stream.flush()
    stream.seek(0)
    digest = hashlib.sha256()
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def _json_value_type(value: object) -> str:
    """Return the closed JSON type name used in predicate evidence."""

    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unsupported"


def _actual_metadata(value: object) -> dict[str, object]:
    """Close actual predicate evidence without persisting the resolved value."""

    result: dict[str, object] = {
        "type": _json_value_type(value),
        "canonical_sha256": _sha256_bytes(_canonical_json(value)),
    }
    if isinstance(value, (str, list, dict)):
        result["length"] = len(value)
    return result


def _darwin_libproc() -> Any | None:
    try:
        libproc = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        libproc.proc_listpids.argtypes = [
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        libproc.proc_listpids.restype = ctypes.c_int
        libproc.proc_pidinfo.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint64,
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        libproc.proc_pidinfo.restype = ctypes.c_int
    except (AttributeError, OSError):
        return None
    return libproc


def _darwin_list_pids(
    libproc: Any,
    selector: int,
    selector_value: int,
) -> set[int] | None:
    """List Darwin PIDs with bounded growth and no silent full-buffer truncation."""

    ctypes.set_errno(0)
    required_bytes = libproc.proc_listpids(selector, selector_value, None, 0)
    if required_bytes < 0:
        return None
    if required_bytes == 0:
        return set() if ctypes.get_errno() in (0, errno.ESRCH) else None
    pid_size = ctypes.sizeof(ctypes.c_int)
    capacity_bytes = max(
        required_bytes * 2,
        required_bytes + DARWIN_PID_LIST_SLACK_BYTES,
        DARWIN_PID_LIST_SLACK_BYTES,
    )
    capacity_bytes -= capacity_bytes % pid_size
    for _attempt in range(DARWIN_PID_LIST_ATTEMPTS):
        pid_buffer = (ctypes.c_int * (capacity_bytes // pid_size))()
        ctypes.set_errno(0)
        returned_bytes = libproc.proc_listpids(
            selector,
            selector_value,
            pid_buffer,
            ctypes.sizeof(pid_buffer),
        )
        if returned_bytes < 0 or returned_bytes > ctypes.sizeof(pid_buffer):
            return None
        if returned_bytes == 0:
            return set() if ctypes.get_errno() in (0, errno.ESRCH) else None
        if returned_bytes % pid_size != 0:
            return None
        if returned_bytes < ctypes.sizeof(pid_buffer):
            return {
                pid
                for pid in pid_buffer[: returned_bytes // pid_size]
                if pid > 0
            }
        capacity_bytes *= 2
    return None


def _darwin_process_info(
    libproc: Any,
    pid: int,
) -> tuple[bool, tuple[int, str] | None]:
    """Return strict Darwin process info; `None` means a verified exit race."""

    info = ctypes.create_string_buffer(DARWIN_PROC_PIDTBSDINFO_SIZE)
    ctypes.set_errno(0)
    try:
        info_bytes = libproc.proc_pidinfo(
            pid,
            DARWIN_PROC_PIDTBSDINFO,
            0,
            info,
            DARWIN_PROC_PIDTBSDINFO_SIZE,
        )
    except (AttributeError, OSError):
        return False, None
    if info_bytes == 0:
        inspection_errno = ctypes.get_errno()
        if inspection_errno == errno.ESRCH:
            return True, None
        if inspection_errno in (errno.EACCES, errno.EPERM):
            return False, None
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True, None
        except PermissionError:
            return False, None
        except OSError:
            return False, None
        return False, None
    if info_bytes != DARWIN_PROC_PIDTBSDINFO_SIZE:
        return False, None
    status = int.from_bytes(info.raw[4:8], sys.byteorder)
    parent_pid = int.from_bytes(info.raw[16:20], sys.byteorder)
    state = "Z" if status == DARWIN_PROC_ZOMBIE_STATUS else str(status)
    return True, (parent_pid, state)


def _darwin_descendant_snapshot(
    parent_pid: int,
) -> tuple[dict[int, tuple[int, str]], bool]:
    """Return every discovered Darwin descendant plus traversal completeness."""

    libproc = _darwin_libproc()
    if libproc is None:
        return {}, False
    snapshot: dict[int, tuple[int, str]] = {parent_pid: (0, "?")}
    owner_edges: dict[int, int] = {}
    pending = [parent_pid]
    inspected: set[int] = set()
    complete = True
    while pending:
        owner_pid = pending.pop()
        if owner_pid in inspected:
            continue
        inspected.add(owner_pid)
        inspection_ok, process_info = _darwin_process_info(libproc, owner_pid)
        if not inspection_ok or process_info is None:
            complete = False
            continue
        if owner_pid == parent_pid:
            snapshot[owner_pid] = process_info
        else:
            snapshot[owner_pid] = (owner_edges[owner_pid], process_info[1])
        children = _darwin_list_pids(
            libproc,
            DARWIN_PROC_PPID_ONLY,
            owner_pid,
        )
        if children is None:
            complete = False
            continue
        for child_pid in children:
            if child_pid in inspected or child_pid in owner_edges:
                continue
            owner_edges[child_pid] = owner_pid
            snapshot[child_pid] = (owner_pid, "?")
            pending.append(child_pid)
    return snapshot, complete


def _darwin_process_snapshot(
    parent_pid: int | None = None,
) -> dict[int, tuple[int, str]] | None:
    """Read Darwin process data without depending on a permitted `ps`."""

    if parent_pid is not None:
        snapshot, complete = _darwin_descendant_snapshot(parent_pid)
        return snapshot if complete else None
    libproc = _darwin_libproc()
    if libproc is None:
        return None
    pids = _darwin_list_pids(libproc, DARWIN_PROC_ALL_PIDS, 0)
    if pids is None or not pids:
        return None

    snapshot: dict[int, tuple[int, str]] = {}
    for pid in pids:
        inspection_ok, process_info = _darwin_process_info(libproc, pid)
        if not inspection_ok:
            return None
        if process_info is None:
            continue
        snapshot[pid] = process_info
    return snapshot


def _ps_process_snapshot() -> dict[int, tuple[int, str]] | None:
    """Read a bounded POSIX PID/PPID/state snapshot from `ps`."""

    try:
        completed = subprocess.run(
            ["ps", "-axo", "pid=,ppid=,stat="],
            check=False,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_FINAL_WAIT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    snapshot: dict[int, tuple[int, str]] = {}
    try:
        for line in completed.stdout.splitlines():
            fields = line.split(None, 2)
            if len(fields) != 3:
                continue
            pid, parent_pid = int(fields[0]), int(fields[1])
            snapshot[pid] = (parent_pid, fields[2])
    except ValueError:
        return None
    return snapshot


def _posix_process_snapshot(
    parent_pid: int | None = None,
) -> dict[int, tuple[int, str]] | None:
    """Return a POSIX process snapshot, or None when inspection is unavailable."""

    if sys.platform == "darwin":
        return _darwin_process_snapshot(parent_pid)
    return _ps_process_snapshot()


def _posix_descendant_snapshot(
    parent_pid: int,
) -> tuple[dict[int, tuple[int, str]], bool]:
    """Return a partial descendant snapshot and explicit inspection completeness."""

    if sys.platform == "darwin":
        return _darwin_descendant_snapshot(parent_pid)
    snapshot = _ps_process_snapshot()
    if snapshot is None:
        return {}, False
    return snapshot, parent_pid in snapshot


def _known_posix_process_snapshot(
    pids: set[int],
) -> dict[int, tuple[int, str]] | None:
    """Inspect only known Darwin descendants; other POSIX hosts retain `ps`."""

    if sys.platform != "darwin":
        return _ps_process_snapshot()
    libproc = _darwin_libproc()
    if libproc is None:
        return None
    snapshot: dict[int, tuple[int, str]] = {}
    for pid in pids:
        inspection_ok, process_info = _darwin_process_info(libproc, pid)
        if not inspection_ok:
            return None
        if process_info is not None:
            snapshot[pid] = process_info
    return snapshot


def _surviving_posix_pids(
    pids: set[int],
    snapshot: dict[int, tuple[int, str]],
) -> set[int]:
    """Find live descendants and fail closed when a live PID evades inspection."""

    survivors: set[int] = set()
    for pid in pids:
        if pid in snapshot:
            if not snapshot[pid][1].startswith("Z"):
                survivors.add(pid)
            continue
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        except PermissionError:
            survivors.add(pid)
        except OSError:
            survivors.add(pid)
        else:
            survivors.add(pid)
    return survivors


def _recursive_descendants(
    parent_pid: int,
    snapshot: dict[int, tuple[int, str]],
) -> set[int]:
    """Resolve every descendant from one stable process-table snapshot."""

    children: dict[int, set[int]] = {}
    for pid, (owner_pid, _state) in snapshot.items():
        children.setdefault(owner_pid, set()).add(pid)
    descendants: set[int] = set()
    pending = list(children.get(parent_pid, ()))
    while pending:
        pid = pending.pop()
        if pid in descendants:
            continue
        descendants.add(pid)
        pending.extend(children.get(pid, ()))
    return descendants


def _signal_pids(pids: set[int], signal_number: int) -> None:
    for pid in sorted(pids, reverse=True):
        try:
            os.kill(pid, signal_number)
        except (ProcessLookupError, PermissionError):
            continue


def _kill_posix_group(process: subprocess.Popen[bytes], signal_number: int) -> None:
    try:
        os.killpg(process.pid, signal_number)
    except (ProcessLookupError, PermissionError):
        if process.poll() is None:
            try:
                os.kill(process.pid, signal_number)
            except (ProcessLookupError, PermissionError):
                pass


def _terminate_posix_process_tree(process: subprocess.Popen[bytes]) -> bool:
    """Terminate the producer and descendants, including children in new sessions."""

    inspection_ok = True
    complete_discovery = False
    descendants: set[int] = set()
    discovery_deadline = time.monotonic() + TIMEOUT_DESCENDANT_DISCOVERY_SECONDS
    while process.poll() is None and time.monotonic() < discovery_deadline:
        snapshot, snapshot_complete = _posix_descendant_snapshot(process.pid)
        descendants.update(_recursive_descendants(process.pid, snapshot))
        if not snapshot_complete or process.pid not in snapshot:
            inspection_ok = False
            break
        complete_discovery = True
        time.sleep(TIMEOUT_POLL_SECONDS)

    if not complete_discovery:
        inspection_ok = False
    if process.poll() is not None:
        inspection_ok = False
    _signal_pids(descendants, signal.SIGTERM)
    _kill_posix_group(process, signal.SIGTERM)
    terminate_deadline = time.monotonic() + TIMEOUT_TERMINATE_GRACE_SECONDS
    while process.poll() is None and time.monotonic() < terminate_deadline:
        known_snapshot = _known_posix_process_snapshot(descendants)
        if known_snapshot is None:
            inspection_ok = False
            break
        _signal_pids(
            _surviving_posix_pids(descendants, known_snapshot),
            signal.SIGTERM,
        )
        time.sleep(TIMEOUT_POLL_SECONDS)

    _signal_pids(descendants, signal.SIGKILL)
    _kill_posix_group(process, signal.SIGKILL)
    if process.poll() is None:
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=TIMEOUT_FINAL_WAIT_SECONDS)
    except subprocess.TimeoutExpired:
        return False

    final_snapshot = _known_posix_process_snapshot(descendants)
    if final_snapshot is None:
        return False
    survivors = _surviving_posix_pids(descendants, final_snapshot)
    if survivors:
        _signal_pids(survivors, signal.SIGKILL)
        time.sleep(TIMEOUT_POLL_SECONDS)
        final_snapshot = _known_posix_process_snapshot(survivors)
        if final_snapshot is None:
            return False
        survivors = _surviving_posix_pids(survivors, final_snapshot)
    return inspection_ok and not survivors


def _terminate_windows_process_tree(process: subprocess.Popen[bytes]) -> bool:
    """Use taskkill's recursive contract, with a bounded direct-process fallback."""

    taskkill_ok = False
    try:
        completed = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=TIMEOUT_FINAL_WAIT_SECONDS,
        )
        taskkill_ok = completed.returncode == 0
    except (OSError, subprocess.SubprocessError):
        taskkill_ok = False
    if process.poll() is None:
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=TIMEOUT_FINAL_WAIT_SECONDS)
    except subprocess.TimeoutExpired:
        return False
    return taskkill_ok and process.poll() is not None


def _terminate_process_tree(
    process: subprocess.Popen[bytes],
    *,
    platform_name: str | None = None,
) -> bool:
    """Dispatch to a testable, fail-closed platform process-tree cleanup."""

    platform = os.name if platform_name is None else platform_name
    if platform == "nt":
        return _terminate_windows_process_tree(process)
    if platform == "posix":
        return _terminate_posix_process_tree(process)
    try:
        process.kill()
        process.wait(timeout=TIMEOUT_FINAL_WAIT_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return False


def _producer_result_without_execution(
    producer: dict[str, Any],
    *,
    status: str,
    reason: str,
) -> dict[str, object]:
    return {
        "id": producer["id"],
        "argv": producer["argv"],
        "depends_on": producer["depends_on"],
        "timeout_seconds": producer["timeout_seconds"],
        "status": status,
        "exit_code": None,
        "timed_out": False,
        "stdout_sha256": None,
        "stderr_sha256": None,
        "reports": [],
        "failure_reason_codes": [reason],
        "source_unchanged": True,
    }


def _topological_producers(producers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = {row["id"]: row for row in producers}
    order: list[dict[str, Any]] = []
    visited: set[str] = set()

    def visit(producer_id: str) -> None:
        if producer_id in visited:
            return
        for dependency in rows[producer_id]["depends_on"]:
            visit(dependency)
        visited.add(producer_id)
        order.append(rows[producer_id])

    for producer in producers:
        visit(producer["id"])
    return order


def _run_producers(
    root: Path,
    producers: list[dict[str, Any]],
    initial_tree: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]], dict[str, object]]:
    results: list[dict[str, object]] = []
    by_id: dict[str, dict[str, object]] = {}
    current_tree = initial_tree
    executed_argv: set[tuple[str, ...]] = set()
    for producer in _topological_producers(producers):
        producer_id = producer["id"]
        dependencies = [by_id[item] for item in producer["depends_on"]]
        if any(item["status"] != "pass" for item in dependencies):
            result = _producer_result_without_execution(
                producer, status="not_run", reason="dependency-not-pass"
            )
            results.append(result)
            by_id[producer_id] = result
            continue

        canonical_argv = tuple(producer["argv"])
        if canonical_argv in executed_argv:
            result = _producer_result_without_execution(
                producer, status="fail", reason="duplicate-argv"
            )
            results.append(result)
            by_id[producer_id] = result
            continue
        executed_argv.add(canonical_argv)
        report_before = {
            path: _file_snapshot(root / path) for path in producer["reports"]
        }
        command = [sys.executable, *producer["argv"][1:]]
        exit_code: int | None = None
        timed_out = False
        process_started = False
        failure_reason_codes: list[str] = []
        with tempfile.TemporaryFile(mode="w+b") as stdout_stream, tempfile.TemporaryFile(
            mode="w+b"
        ) as stderr_stream:
            try:
                process = subprocess.Popen(
                    command,
                    cwd=root,
                    stdout=stdout_stream,
                    stderr=stderr_stream,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                    start_new_session=os.name == "posix",
                    creationflags=(
                        subprocess.CREATE_NEW_PROCESS_GROUP
                        if os.name == "nt"
                        else 0
                    ),
                )
                process_started = True
                try:
                    exit_code = process.wait(timeout=producer["timeout_seconds"])
                except subprocess.TimeoutExpired:
                    timed_out = True
                    failure_reason_codes.append("process-timeout")
                    if not _terminate_process_tree(process):
                        failure_reason_codes.append(
                            "process-tree-cleanup-failed"
                        )
            except OSError:
                failure_reason_codes.append("process-start-failed")
            stdout_sha256 = _sha256_stream(stdout_stream)
            stderr_sha256 = _sha256_stream(stderr_stream)
        if process_started and not timed_out and exit_code != 0:
            failure_reason_codes.append("process-exit-nonzero")
        report_results: list[dict[str, object]] = []
        for report in producer["reports"]:
            path = root / report
            after = _file_snapshot(path)
            fresh = _fresh_report(report_before[report], after)
            payload: object | None = None
            json_object = False
            if after["exists"]:
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    json_object = isinstance(payload, dict)
                except (OSError, UnicodeError, json.JSONDecodeError):
                    payload = None
            if not fresh:
                failure_reason_codes.append("report-not-refreshed")
            if not json_object:
                failure_reason_codes.append("report-not-json-object")
            report_results.append(
                {
                    "path": report,
                    "fresh": fresh,
                    "json_object": json_object,
                    "sha256": after["sha256"],
                }
            )
        next_tree = input_tree_digest(root)
        if timed_out:
            time.sleep(TIMEOUT_TREE_RECHECK_SECONDS)
            settled_tree = input_tree_digest(root)
            source_unchanged = (
                current_tree == next_tree == settled_tree
            )
            next_tree = settled_tree
        else:
            source_unchanged = current_tree == next_tree
        if not source_unchanged:
            failure_reason_codes.append("source-tree-mutated")
        failure_reason_codes = list(dict.fromkeys(failure_reason_codes))
        status = "timeout" if timed_out else "pass" if not failure_reason_codes else "fail"
        result = {
            "id": producer_id,
            "argv": producer["argv"],
            "depends_on": producer["depends_on"],
            "timeout_seconds": producer["timeout_seconds"],
            "status": status,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "stdout_sha256": None if status == "pass" else stdout_sha256,
            "stderr_sha256": None if status == "pass" else stderr_sha256,
            "reports": report_results,
            "failure_reason_codes": failure_reason_codes,
            "source_unchanged": source_unchanged,
        }
        results.append(result)
        by_id[producer_id] = result
        current_tree = next_tree
    return results, by_id, current_tree


def evaluate_operator(actual: object, operator: str, expected: object) -> bool:
    """Evaluate one closed predicate operator."""

    if operator == "equals":
        return actual == expected and type(actual) is type(expected)
    if operator == "not_equals":
        return not (actual == expected and type(actual) is type(expected))
    if operator in {"greater_than_or_equal", "less_than_or_equal"}:
        if (
            isinstance(actual, bool)
            or isinstance(expected, bool)
            or not isinstance(actual, (int, float))
            or not isinstance(expected, (int, float))
        ):
            return False
        return actual >= expected if operator == "greater_than_or_equal" else actual <= expected
    if operator in {"contains", "not_contains"}:
        try:
            contained = expected in actual  # type: ignore[operator]
        except (TypeError, ValueError):
            return False
        return contained if operator == "contains" else not contained
    if operator not in PRINCIPLE_PREDICATE_OPERATORS:
        raise ValueError(f"unsupported predicate operator {operator!r}")
    return False


def _expected_value(
    predicate: dict[str, Any],
    authorities: dict[str, object],
) -> tuple[object, dict[str, str] | None]:
    if "expected" in predicate:
        return predicate["expected"], None
    provenance = predicate["expected_from"]
    authority_id = provenance["authority"]
    return (
        resolve_json_pointer(authorities[authority_id], provenance["pointer"]),
        {"authority": authority_id, "pointer": provenance["pointer"]},
    )


def _evaluate_outcomes(
    root: Path,
    outcomes: list[dict[str, Any]],
    producer_results: dict[str, dict[str, object]],
    authority_values: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    results: list[dict[str, object]] = []
    by_id: dict[str, dict[str, object]] = {}
    report_cache: dict[str, object] = {}
    for outcome in outcomes:
        producer = producer_results[outcome["producer"]]
        predicate_results: list[dict[str, object]] = []
        for predicate in outcome["predicates"]:
            source = predicate["source"]
            if source == "process":
                document: object = {
                    "exit_code": producer["exit_code"],
                    "status": producer["status"],
                }
            else:
                if source not in report_cache:
                    try:
                        report_cache[source] = json.loads(
                            (root / source).read_text(encoding="utf-8")
                        )
                    except (OSError, UnicodeError, json.JSONDecodeError):
                        report_cache[source] = None
                document = report_cache[source]
            expected, expected_from = _expected_value(predicate, authority_values)
            resolution_status = "resolved"
            actual_metadata: dict[str, object] | None
            try:
                actual = resolve_json_pointer(document, predicate["pointer"])
                passed = evaluate_operator(actual, predicate["operator"], expected)
                actual_metadata = _actual_metadata(actual)
            except (TypeError, ValueError):
                actual_metadata = None
                passed = False
                resolution_status = "pointer-error"
            result: dict[str, object] = {
                "source": source,
                "pointer": predicate["pointer"],
                "operator": predicate["operator"],
                "expected": expected,
                "actual_metadata": actual_metadata,
                "resolution_status": resolution_status,
                "status": "pass" if passed else "fail",
            }
            if expected_from is not None:
                result["expected_from"] = expected_from
            predicate_results.append(result)
        if producer["status"] == "not_run":
            status = "not_run"
        elif producer["status"] != "pass":
            status = "fail"
        else:
            status = "pass" if all(item["status"] == "pass" for item in predicate_results) else "fail"
        result = {
            "id": outcome["id"],
            "producer": outcome["producer"],
            "dimensions": outcome["dimensions"],
            "capabilities": outcome["capabilities"],
            "status": status,
            "predicates": predicate_results,
        }
        results.append(result)
        by_id[outcome["id"]] = result
    return results, by_id


def _authoring_status(outcome_ids: list[str], outcomes: dict[str, dict[str, object]]) -> str:
    statuses = [outcomes[outcome_id]["status"] for outcome_id in outcome_ids]
    if all(status == "pass" for status in statuses):
        return "pass"
    if any(status == "fail" for status in statuses):
        return "fail"
    return "not_run"


def _principle_results(
    principles: list[dict[str, Any]],
    outcomes: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for principle in principles:
        authoring_ids = principle["required_outcomes"]["authoring"]
        formal_ids = principle["required_outcomes"]["formal_release"]
        authoring = _authoring_status(authoring_ids, outcomes)
        formal_all = [*authoring_ids, *formal_ids]
        formal = (
            "pass"
            if authoring == "pass" and all(outcomes[item]["status"] == "pass" for item in formal_all)
            else "blocked"
        )
        status = "pass" if formal == "pass" else "partial" if authoring == "pass" else "fail"
        results.append(
            {
                "id": principle["id"],
                "name": principle["name"],
                "required_dimensions": principle["required_dimensions"],
                "required_outcomes": principle["required_outcomes"],
                "authoring_status": authoring,
                "formal_release_status": formal,
                "status": status,
            }
        )
    return results


def _authority_results(
    contract: dict[str, Any],
    producer_results: dict[str, dict[str, object]],
    outcome_results: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    acceptance = contract["principle_acceptance_contract"]
    consumers: dict[str, list[str]] = {row["id"]: [] for row in acceptance["authorities"]}
    producer_outcomes: dict[str, list[str]] = {}
    for outcome in acceptance["outcomes"]:
        producer_outcomes.setdefault(outcome["producer"], []).append(outcome["id"])
    for producer in acceptance["producers"]:
        for authority_id in producer["authority_inputs"]:
            consumers[authority_id].append(producer["id"])
    results: list[dict[str, object]] = []
    for authority in acceptance["authorities"]:
        value = resolve_json_pointer(contract, authority["pointer"])
        results.append(
            {
                "id": authority["id"],
                "source": "src/control-model/core-contracts.json",
                "pointer": authority["pointer"],
                "value_sha256": _sha256_bytes(_canonical_json(value)),
                "consumer_results": [
                    {
                        "producer": producer_id,
                        "producer_status": producer_results[producer_id]["status"],
                        "outcomes": [
                            {
                                "id": outcome_id,
                                "status": outcome_results[outcome_id]["status"],
                            }
                            for outcome_id in producer_outcomes.get(producer_id, [])
                        ],
                    }
                    for producer_id in consumers[authority["id"]]
                ],
            }
        )
    return results


def _invalid_report(
    root: Path,
    contract_sha256: str | None,
    errors: list[str],
) -> dict[str, object]:
    tree = input_tree_digest(root)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "kind": "changeforge.core_principles_outcomes",
        "contract_source": CANONICAL_CONTRACT_SOURCE,
        "contract_sha256": contract_sha256,
        "input_tree": {"pre": tree, "post": tree, "unchanged": True},
        "principles_status": "fail",
        "authoring_principles_status": "fail",
        "formal_principles_status": "blocked",
        "limitations": EVIDENCE_LIMITATIONS,
        "uncovered_mandatory_release_gates": UNCOVERED_MANDATORY_RELEASE_GATES,
        "contract_errors": errors,
        "command_execution_count": 0,
        "producers": [],
        "outcomes": [],
        "authorities": [],
        "principles": [],
    }


def evaluate(
    root: Path,
    contract: dict[str, Any],
    *,
    contract_sha256: str | None = None,
) -> dict[str, object]:
    """Run one complete outcome evaluation and return the deterministic report."""

    errors = validate_principle_acceptance_contract(contract, root)
    if errors:
        return _invalid_report(root, contract_sha256, errors)
    acceptance = contract["principle_acceptance_contract"]
    pre_tree = input_tree_digest(root)
    producers, producers_by_id, post_tree = _run_producers(
        root, acceptance["producers"], pre_tree
    )
    authority_values = {
        authority["id"]: resolve_json_pointer(contract, authority["pointer"])
        for authority in acceptance["authorities"]
    }
    outcomes, outcomes_by_id = _evaluate_outcomes(
        root,
        acceptance["outcomes"],
        producers_by_id,
        authority_values,
    )
    principles = _principle_results(contract["core_principles"], outcomes_by_id)
    authoring = "pass" if all(item["authoring_status"] == "pass" for item in principles) else "fail"
    formal = (
        "pass"
        if authoring == "pass" and all(item["formal_release_status"] == "pass" for item in principles)
        else "blocked"
    )
    status = "pass" if formal == "pass" else "partial" if authoring == "pass" else "fail"
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "kind": "changeforge.core_principles_outcomes",
        "contract_source": CANONICAL_CONTRACT_SOURCE,
        "contract_sha256": contract_sha256,
        "input_tree": {
            "pre": pre_tree,
            "post": post_tree,
            "unchanged": pre_tree == post_tree,
        },
        "principles_status": status,
        "authoring_principles_status": authoring,
        "formal_principles_status": formal,
        "limitations": EVIDENCE_LIMITATIONS,
        "uncovered_mandatory_release_gates": UNCOVERED_MANDATORY_RELEASE_GATES,
        "contract_errors": [],
        "command_execution_count": sum(item["status"] != "not_run" for item in producers),
        "producers": producers,
        "outcomes": outcomes,
        "authorities": _authority_results(
            contract, producers_by_id, outcomes_by_id
        ),
        "principles": principles,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Core Principles Outcomes",
        "",
        "This report evaluates the Core Principles sub-gates. It is not a repository formal release decision.",
        "",
        f"- Core Principles aggregate: `{report['principles_status']}`",
        f"- Core Principles authoring sub-gate: `{report['authoring_principles_status']}`",
        f"- Core Principles formal sub-gate: `{report['formal_principles_status']}`",
        f"- Input tree: `{report['input_tree']['post']['sha256']}`",
        "",
        "| Principle | Authoring sub-gate | Formal sub-gate | Outcome |",
        "| --- | --- | --- | --- |",
    ]
    for principle in report["principles"]:
        lines.append(
            f"| {principle['name']} | `{principle['authoring_status']}` | "
            f"`{principle['formal_release_status']}` | `{principle['status']}` |"
        )
    if report["contract_errors"]:
        lines.extend(["", "## Contract Errors", ""])
        lines.extend(f"- {error}" for error in report["contract_errors"])
    lines.extend(["", "## Evidence Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(["", "## Mandatory Repository Release Gates Not Covered", ""])
    lines.extend(
        f"- `{item}`" for item in report["uncovered_mandatory_release_gates"]
    )
    return "\n".join(lines) + "\n"


def write_reports(root: Path, report: dict[str, Any]) -> None:
    json_path = root / JSON_REPORT
    markdown_path = root / MARKDOWN_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")


def _saved_report_schema_errors(report: object) -> list[str]:
    """Validate every persisted collection before semantic report validation."""

    errors: list[str] = []

    def add(message: str) -> None:
        if len(errors) < MAX_SAVED_REPORT_SCHEMA_ERRORS:
            errors.append(message)

    def closed_object(
        value: object,
        fields: set[str],
        context: str,
    ) -> dict[str, object] | None:
        if type(value) is not dict:
            add(f"{context} must be an object")
            return None
        assert isinstance(value, dict)
        if set(value) != fields:
            add(f"{context} fields do not match the closed schema")
            return None
        return value

    def closed_list(value: object, context: str) -> list[object] | None:
        if type(value) is not list:
            add(f"{context} must be a list")
            return None
        assert isinstance(value, list)
        if len(value) > MAX_SAVED_REPORT_COLLECTION_ITEMS:
            add(f"{context} exceeds the closed collection limit")
            return None
        return value

    def string(value: object, context: str, *, nonempty: bool = True) -> bool:
        if type(value) is not str or (nonempty and not value):
            add(f"{context} must be {'a non-empty' if nonempty else 'a'} string")
            return False
        return True

    def report_path(value: object, context: str) -> bool:
        if not string(value, context):
            return False
        assert isinstance(value, str)
        path = PurePosixPath(value)
        if (
            path.is_absolute()
            or not path.parts
            or path.parts[0] != "reports"
            or path.suffix != ".json"
            or ".." in path.parts
        ):
            add(f"{context} must be a safe reports/*.json path")
            return False
        return True

    def boolean(value: object, context: str) -> bool:
        if type(value) is not bool:
            add(f"{context} must be a boolean")
            return False
        return True

    def integer(
        value: object,
        context: str,
        *,
        nullable: bool = False,
        nonnegative: bool = False,
    ) -> bool:
        if nullable and value is None:
            return True
        if type(value) is not int or (nonnegative and value < 0):
            qualifier = "a non-negative integer" if nonnegative else "an integer"
            if nullable:
                qualifier += " or null"
            add(f"{context} must be {qualifier}")
            return False
        return True

    def sha256(value: object, context: str, *, nullable: bool = False) -> bool:
        if nullable and value is None:
            return True
        if (
            type(value) is not str
            or len(value) != 64
            or any(char not in "0123456789abcdef" for char in value)
        ):
            add(
                f"{context} must be lowercase SHA-256"
                + (" or null" if nullable else "")
            )
            return False
        return True

    def closed_value(
        value: object,
        allowed: set[str],
        context: str,
    ) -> bool:
        if type(value) is not str or value not in allowed:
            add(f"{context} is not in its closed value set")
            return False
        return True

    def string_list(value: object, context: str) -> bool:
        items = closed_list(value, context)
        if items is None:
            return False
        valid = True
        for index, item in enumerate(items):
            if len(errors) >= MAX_SAVED_REPORT_SCHEMA_ERRORS:
                break
            valid = string(item, f"{context}[{index}]") and valid
        return valid

    def json_value(value: object, context: str) -> bool:
        pending = [value]
        visited = 0
        while pending:
            current = pending.pop()
            visited += 1
            if visited > MAX_SAVED_REPORT_COLLECTION_ITEMS:
                add(f"{context} exceeds the closed JSON value limit")
                return False
            if current is None or type(current) in {str, bool, int}:
                continue
            if type(current) is float:
                if not math.isfinite(current):
                    add(f"{context} must contain only finite JSON numbers")
                    return False
                continue
            if type(current) is list:
                pending.extend(current)
                continue
            if type(current) is dict:
                if any(type(key) is not str for key in current):
                    add(f"{context} JSON object keys must be strings")
                    return False
                pending.extend(current.values())
                continue
            add(f"{context} must be a closed JSON value")
            return False
        return True

    top_fields = {
        "schema_version",
        "kind",
        "contract_source",
        "contract_sha256",
        "input_tree",
        "principles_status",
        "authoring_principles_status",
        "formal_principles_status",
        "limitations",
        "uncovered_mandatory_release_gates",
        "contract_errors",
        "command_execution_count",
        "producers",
        "outcomes",
        "authorities",
        "principles",
    }
    top = closed_object(report, top_fields, "core principles report")
    if top is None:
        return errors

    integer(top["schema_version"], "core principles report.schema_version")
    string(top["kind"], "core principles report.kind")
    string(top["contract_source"], "core principles report.contract_source")
    sha256(
        top["contract_sha256"],
        "core principles report.contract_sha256",
        nullable=True,
    )
    closed_value(
        top["principles_status"],
        {"pass", "partial", "fail"},
        "core principles report.principles_status",
    )
    closed_value(
        top["authoring_principles_status"],
        {"pass", "fail"},
        "core principles report.authoring_principles_status",
    )
    closed_value(
        top["formal_principles_status"],
        {"pass", "blocked"},
        "core principles report.formal_principles_status",
    )
    string_list(top["limitations"], "core principles report.limitations")
    string_list(
        top["uncovered_mandatory_release_gates"],
        "core principles report.uncovered_mandatory_release_gates",
    )
    string_list(
        top["contract_errors"], "core principles report.contract_errors"
    )
    integer(
        top["command_execution_count"],
        "core principles report.command_execution_count",
        nonnegative=True,
    )

    input_tree = closed_object(
        top["input_tree"],
        {"pre", "post", "unchanged"},
        "core principles report.input_tree",
    )
    if input_tree is not None:
        boolean(
            input_tree["unchanged"],
            "core principles report.input_tree.unchanged",
        )
        for stage in ("pre", "post"):
            digest = closed_object(
                input_tree[stage],
                {"sha256", "file_count"},
                f"core principles report.input_tree.{stage}",
            )
            if digest is None:
                continue
            sha256(
                digest["sha256"],
                f"core principles report.input_tree.{stage}.sha256",
            )
            integer(
                digest["file_count"],
                f"core principles report.input_tree.{stage}.file_count",
                nonnegative=True,
            )

    producer_fields = {
        "id",
        "argv",
        "depends_on",
        "timeout_seconds",
        "status",
        "exit_code",
        "timed_out",
        "stdout_sha256",
        "stderr_sha256",
        "reports",
        "failure_reason_codes",
        "source_unchanged",
    }
    artifact_fields = {"path", "fresh", "json_object", "sha256"}
    producers = closed_list(top["producers"], "core principles report.producers")
    if producers is not None:
        for index, value in enumerate(producers):
            if len(errors) >= MAX_SAVED_REPORT_SCHEMA_ERRORS:
                break
            context = f"core principles report.producers[{index}]"
            producer = closed_object(value, producer_fields, context)
            if producer is None:
                continue
            string(producer["id"], f"{context}.id")
            string_list(producer["argv"], f"{context}.argv")
            string_list(producer["depends_on"], f"{context}.depends_on")
            integer(
                producer["timeout_seconds"],
                f"{context}.timeout_seconds",
                nonnegative=True,
            )
            closed_value(
                producer["status"],
                {"pass", "fail", "timeout", "not_run"},
                f"{context}.status",
            )
            integer(
                producer["exit_code"], f"{context}.exit_code", nullable=True
            )
            boolean(producer["timed_out"], f"{context}.timed_out")
            sha256(
                producer["stdout_sha256"],
                f"{context}.stdout_sha256",
                nullable=True,
            )
            sha256(
                producer["stderr_sha256"],
                f"{context}.stderr_sha256",
                nullable=True,
            )
            string_list(
                producer["failure_reason_codes"],
                f"{context}.failure_reason_codes",
            )
            boolean(
                producer["source_unchanged"], f"{context}.source_unchanged"
            )
            artifacts = closed_list(producer["reports"], f"{context}.reports")
            if artifacts is None:
                continue
            for artifact_index, artifact_value in enumerate(artifacts):
                artifact_context = f"{context}.reports[{artifact_index}]"
                artifact = closed_object(
                    artifact_value, artifact_fields, artifact_context
                )
                if artifact is None:
                    continue
                report_path(artifact["path"], f"{artifact_context}.path")
                boolean(artifact["fresh"], f"{artifact_context}.fresh")
                boolean(
                    artifact["json_object"],
                    f"{artifact_context}.json_object",
                )
                sha256(
                    artifact["sha256"],
                    f"{artifact_context}.sha256",
                    nullable=True,
                )

    outcome_fields = {
        "id",
        "producer",
        "dimensions",
        "capabilities",
        "status",
        "predicates",
    }
    predicate_fields = {
        "source",
        "pointer",
        "operator",
        "expected",
        "actual_metadata",
        "resolution_status",
        "status",
    }
    outcomes = closed_list(top["outcomes"], "core principles report.outcomes")
    if outcomes is not None:
        for index, value in enumerate(outcomes):
            if len(errors) >= MAX_SAVED_REPORT_SCHEMA_ERRORS:
                break
            context = f"core principles report.outcomes[{index}]"
            outcome = closed_object(value, outcome_fields, context)
            if outcome is None:
                continue
            string(outcome["id"], f"{context}.id")
            string(outcome["producer"], f"{context}.producer")
            string_list(outcome["dimensions"], f"{context}.dimensions")
            string_list(outcome["capabilities"], f"{context}.capabilities")
            closed_value(
                outcome["status"],
                {"pass", "fail", "not_run"},
                f"{context}.status",
            )
            predicates = closed_list(
                outcome["predicates"], f"{context}.predicates"
            )
            if predicates is None:
                continue
            for predicate_index, predicate_value in enumerate(predicates):
                predicate_context = (
                    f"{context}.predicates[{predicate_index}]"
                )
                if type(predicate_value) is not dict:
                    add(f"{predicate_context} must be an object")
                    continue
                predicate_keys = set(predicate_value)
                if predicate_keys != predicate_fields and predicate_keys != {
                    *predicate_fields,
                    "expected_from",
                }:
                    add(
                        f"{predicate_context} fields do not match the closed schema"
                    )
                    continue
                predicate = predicate_value
                string(predicate["source"], f"{predicate_context}.source")
                string(predicate["pointer"], f"{predicate_context}.pointer")
                closed_value(
                    predicate["operator"],
                    PRINCIPLE_PREDICATE_OPERATORS,
                    f"{predicate_context}.operator",
                )
                json_value(
                    predicate["expected"], f"{predicate_context}.expected"
                )
                closed_value(
                    predicate["resolution_status"],
                    {"resolved", "pointer-error"},
                    f"{predicate_context}.resolution_status",
                )
                closed_value(
                    predicate["status"],
                    {"pass", "fail"},
                    f"{predicate_context}.status",
                )
                if "expected_from" in predicate:
                    provenance = closed_object(
                        predicate["expected_from"],
                        {"authority", "pointer"},
                        f"{predicate_context}.expected_from",
                    )
                    if provenance is not None:
                        string(
                            provenance["authority"],
                            f"{predicate_context}.expected_from.authority",
                        )
                        string(
                            provenance["pointer"],
                            f"{predicate_context}.expected_from.pointer",
                        )
                metadata_value = predicate["actual_metadata"]
                if predicate["resolution_status"] == "pointer-error":
                    if metadata_value is not None:
                        add(
                            f"{predicate_context}.actual_metadata must be null "
                            "for pointer-error"
                        )
                    continue
                if type(metadata_value) is not dict:
                    add(
                        f"{predicate_context}.actual_metadata must be an object "
                        "for resolved predicates"
                    )
                    continue
                actual_type = metadata_value.get("type")
                metadata_fields = {"type", "canonical_sha256"}
                if type(actual_type) is str and actual_type in {
                    "string",
                    "array",
                    "object",
                }:
                    metadata_fields.add("length")
                metadata = closed_object(
                    metadata_value,
                    metadata_fields,
                    f"{predicate_context}.actual_metadata",
                )
                if metadata is None:
                    continue
                closed_value(
                    metadata["type"],
                    {
                        "null",
                        "boolean",
                        "integer",
                        "number",
                        "string",
                        "array",
                        "object",
                    },
                    f"{predicate_context}.actual_metadata.type",
                )
                sha256(
                    metadata["canonical_sha256"],
                    f"{predicate_context}.actual_metadata.canonical_sha256",
                )
                if "length" in metadata:
                    integer(
                        metadata["length"],
                        f"{predicate_context}.actual_metadata.length",
                        nonnegative=True,
                    )

    authority_fields = {
        "id",
        "source",
        "pointer",
        "value_sha256",
        "consumer_results",
    }
    consumer_fields = {"producer", "producer_status", "outcomes"}
    consumer_outcome_fields = {"id", "status"}
    authorities = closed_list(
        top["authorities"], "core principles report.authorities"
    )
    if authorities is not None:
        for index, value in enumerate(authorities):
            if len(errors) >= MAX_SAVED_REPORT_SCHEMA_ERRORS:
                break
            context = f"core principles report.authorities[{index}]"
            authority = closed_object(value, authority_fields, context)
            if authority is None:
                continue
            string(authority["id"], f"{context}.id")
            string(authority["source"], f"{context}.source")
            string(authority["pointer"], f"{context}.pointer")
            sha256(authority["value_sha256"], f"{context}.value_sha256")
            consumers = closed_list(
                authority["consumer_results"], f"{context}.consumer_results"
            )
            if consumers is None:
                continue
            for consumer_index, consumer_value in enumerate(consumers):
                consumer_context = (
                    f"{context}.consumer_results[{consumer_index}]"
                )
                consumer = closed_object(
                    consumer_value, consumer_fields, consumer_context
                )
                if consumer is None:
                    continue
                string(consumer["producer"], f"{consumer_context}.producer")
                closed_value(
                    consumer["producer_status"],
                    {"pass", "fail", "timeout", "not_run"},
                    f"{consumer_context}.producer_status",
                )
                consumer_outcomes = closed_list(
                    consumer["outcomes"], f"{consumer_context}.outcomes"
                )
                if consumer_outcomes is None:
                    continue
                for outcome_index, outcome_value in enumerate(consumer_outcomes):
                    consumer_outcome_context = (
                        f"{consumer_context}.outcomes[{outcome_index}]"
                    )
                    consumer_outcome = closed_object(
                        outcome_value,
                        consumer_outcome_fields,
                        consumer_outcome_context,
                    )
                    if consumer_outcome is None:
                        continue
                    string(
                        consumer_outcome["id"],
                        f"{consumer_outcome_context}.id",
                    )
                    closed_value(
                        consumer_outcome["status"],
                        {"pass", "fail", "not_run"},
                        f"{consumer_outcome_context}.status",
                    )

    principle_fields = {
        "id",
        "name",
        "required_dimensions",
        "required_outcomes",
        "authoring_status",
        "formal_release_status",
        "status",
    }
    principles = closed_list(
        top["principles"], "core principles report.principles"
    )
    if principles is not None:
        for index, value in enumerate(principles):
            if len(errors) >= MAX_SAVED_REPORT_SCHEMA_ERRORS:
                break
            context = f"core principles report.principles[{index}]"
            principle = closed_object(value, principle_fields, context)
            if principle is None:
                continue
            string(principle["id"], f"{context}.id")
            string(principle["name"], f"{context}.name")
            string_list(
                principle["required_dimensions"],
                f"{context}.required_dimensions",
            )
            required_outcomes = closed_object(
                principle["required_outcomes"],
                {"authoring", "formal_release"},
                f"{context}.required_outcomes",
            )
            if required_outcomes is not None:
                string_list(
                    required_outcomes["authoring"],
                    f"{context}.required_outcomes.authoring",
                )
                string_list(
                    required_outcomes["formal_release"],
                    f"{context}.required_outcomes.formal_release",
                )
            closed_value(
                principle["authoring_status"],
                {"pass", "fail", "not_run"},
                f"{context}.authoring_status",
            )
            closed_value(
                principle["formal_release_status"],
                {"pass", "blocked"},
                f"{context}.formal_release_status",
            )
            closed_value(
                principle["status"],
                {"pass", "partial", "fail"},
                f"{context}.status",
            )
    return errors


def validate_saved_report(root: Path, report: object) -> list[str]:
    """Validate a checked-in report's schema and current input/report truth."""

    schema_errors = _saved_report_schema_errors(report)
    if schema_errors:
        return schema_errors
    assert isinstance(report, dict)
    errors: list[str] = []
    if report["schema_version"] != REPORT_SCHEMA_VERSION or report["kind"] != "changeforge.core_principles_outcomes":
        errors.append("core principles report schema identity is invalid")
    if report["limitations"] != EVIDENCE_LIMITATIONS:
        errors.append("core principles report evidence limitations are incomplete")
    if report["uncovered_mandatory_release_gates"] != UNCOVERED_MANDATORY_RELEASE_GATES:
        errors.append("core principles report uncovered release gates are incomplete")
    contract_source = report["contract_source"]
    contract_path = root / CANONICAL_CONTRACT_SOURCE
    if contract_source != CANONICAL_CONTRACT_SOURCE:
        errors.append(
            "core principles report contract source must be the canonical "
            f"{CANONICAL_CONTRACT_SOURCE}"
        )
    if not contract_path.is_file():
        errors.append("core principles report canonical contract source is missing")
        contract: object = None
    else:
        contract_bytes = contract_path.read_bytes()
        if report["contract_sha256"] != _sha256_bytes(contract_bytes):
            errors.append("core principles report contract hash is stale")
        try:
            contract = json.loads(contract_bytes)
        except json.JSONDecodeError:
            contract = None
            errors.append("core principles report contract source is malformed")
    tree = input_tree_digest(root)
    input_tree = report["input_tree"]
    if not isinstance(input_tree, dict) or set(input_tree) != {"pre", "post", "unchanged"}:
        errors.append("core principles report input tree schema is invalid")
    else:
        if input_tree["pre"] != input_tree["post"] or input_tree["unchanged"] is not True:
            errors.append("core principles report records an input tree mutation")
        if input_tree["post"] != tree:
            errors.append("core principles report input tree digest is stale")
    principles = report["principles"] if isinstance(report["principles"], list) else []
    authoring = "pass" if principles and all(item.get("authoring_status") == "pass" for item in principles if isinstance(item, dict)) and len(principles) == 15 else "fail"
    formal = "pass" if authoring == "pass" and all(item.get("formal_release_status") == "pass" for item in principles if isinstance(item, dict)) and len(principles) == 15 else "blocked"
    status = "pass" if formal == "pass" else "partial" if authoring == "pass" else "fail"
    if (
        report["authoring_principles_status"] != authoring
        or report["formal_principles_status"] != formal
        or report["principles_status"] != status
    ):
        errors.append("core principles report aggregate statuses are inconsistent")
    for producer in report["producers"] if isinstance(report["producers"], list) else []:
        if not isinstance(producer, dict):
            errors.append("core principles report producer entry is invalid")
            continue
        producer_fields = {
            "id",
            "argv",
            "depends_on",
            "timeout_seconds",
            "status",
            "exit_code",
            "timed_out",
            "stdout_sha256",
            "stderr_sha256",
            "reports",
            "failure_reason_codes",
            "source_unchanged",
        }
        if set(producer) != producer_fields:
            errors.append(
                f"core principles producer evidence schema is invalid: {producer.get('id')}"
            )
        for artifact in producer.get("reports", []):
            if not isinstance(artifact, dict):
                errors.append("core principles report artifact entry is invalid")
                continue
            if set(artifact) != {"path", "fresh", "json_object", "sha256"}:
                errors.append("core principles report artifact schema is invalid")
                continue
            path = artifact.get("path")
            if not isinstance(path, str) or not (root / path).is_file():
                errors.append(f"core principles producer report is missing: {path!r}")
            elif artifact.get("sha256") != _sha256_bytes((root / path).read_bytes()):
                errors.append(f"core principles producer report hash is stale: {path}")
            if producer.get("status") == "pass" and (
                artifact.get("fresh") is not True
                or artifact.get("json_object") is not True
            ):
                errors.append(
                    f"passing core principles producer report was not fresh JSON: {path}"
                )
    if isinstance(contract, dict):
        contract_errors = validate_principle_acceptance_contract(contract, root)
        if contract_errors:
            errors.append("core principles report references an invalid outcome contract")
            return errors[:MAX_SAVED_REPORT_SCHEMA_ERRORS]
        if report["contract_errors"]:
            errors.append("core principles report preserves stale contract errors")
        acceptance = contract.get("principle_acceptance_contract", {})
        declared_producers = acceptance.get("producers", [])
        saved_producers = report["producers"] if isinstance(report["producers"], list) else []
        producer_by_id = {
            item.get("id"): item for item in saved_producers if isinstance(item, dict)
        }
        if [item.get("id") for item in saved_producers if isinstance(item, dict)] != [
            item.get("id") for item in _topological_producers(declared_producers)
        ]:
            errors.append("core principles report producer order or identity is stale")
        for declared in declared_producers:
            saved = producer_by_id.get(declared.get("id"))
            if not isinstance(saved, dict):
                continue
            if saved.get("argv") != declared.get("argv") or saved.get(
                "depends_on"
            ) != declared.get("depends_on") or saved.get(
                "timeout_seconds"
            ) != declared.get("timeout_seconds"):
                errors.append(
                    f"core principles producer contract is stale: {declared.get('id')}"
                )
            producer_status = saved.get("status")
            if producer_status not in {"pass", "fail", "timeout", "not_run"}:
                errors.append(
                    f"core principles producer status is invalid: {declared.get('id')}"
                )
            failure_reason_codes = saved.get("failure_reason_codes")
            if (
                not isinstance(failure_reason_codes, list)
                or len(failure_reason_codes) != len(set(failure_reason_codes))
                or any(
                    reason not in PRODUCER_FAILURE_REASON_CODES
                    for reason in failure_reason_codes
                )
            ):
                errors.append(
                    f"core principles producer failure reasons are invalid: {declared.get('id')}"
                )
                failure_reason_codes = []
            if producer_status == "pass" and (
                saved.get("exit_code") != 0
                or saved.get("timed_out") is not False
                or saved.get("source_unchanged") is not True
                or failure_reason_codes
                or saved.get("stdout_sha256") is not None
                or saved.get("stderr_sha256") is not None
            ):
                errors.append(
                    f"passing core principles producer evidence is inconsistent: {declared.get('id')}"
                )
            if producer_status == "timeout" and (
                saved.get("exit_code") is not None
                or saved.get("timed_out") is not True
                or "process-timeout" not in failure_reason_codes
            ):
                errors.append(
                    f"timed-out core principles producer evidence is inconsistent: {declared.get('id')}"
                )
            if producer_status == "not_run" and (
                saved.get("exit_code") is not None
                or saved.get("timed_out") is not False
                or saved.get("stdout_sha256") is not None
                or saved.get("stderr_sha256") is not None
                or failure_reason_codes != ["dependency-not-pass"]
            ):
                errors.append(
                    f"not-run core principles producer evidence is inconsistent: {declared.get('id')}"
                )
            if producer_status in {"fail", "timeout"}:
                for stream_name in ("stdout_sha256", "stderr_sha256"):
                    digest = saved.get(stream_name)
                    if not isinstance(digest, str) or len(digest) != 64 or any(
                        char not in "0123456789abcdef" for char in digest
                    ):
                        errors.append(
                            f"core principles producer {stream_name} is invalid: {declared.get('id')}"
                        )
            artifact_paths = [
                artifact.get("path")
                for artifact in saved.get("reports", [])
                if isinstance(artifact, dict)
            ]
            expected_artifact_paths = (
                [] if producer_status == "not_run" else declared.get("reports")
            )
            if artifact_paths != expected_artifact_paths:
                errors.append(
                    f"core principles producer report list is stale: {declared.get('id')}"
                )
        if report["command_execution_count"] != sum(
            item.get("status") != "not_run"
            for item in saved_producers
            if isinstance(item, dict)
        ):
            errors.append("core principles command execution count is inconsistent")
        authority_values = {
            authority["id"]: resolve_json_pointer(contract, authority["pointer"])
            for authority in acceptance.get("authorities", [])
        }
        if len(producer_by_id) == len(declared_producers):
            expected_outcomes, outcome_by_id = _evaluate_outcomes(
                root,
                acceptance.get("outcomes", []),
                producer_by_id,
                authority_values,
            )
            if report["outcomes"] != expected_outcomes:
                errors.append("core principles report outcome predicates are stale or inconsistent")
            expected_principles = _principle_results(
                contract.get("core_principles", []), outcome_by_id
            )
            if report["principles"] != expected_principles:
                errors.append("core principles report principle statuses are stale or inconsistent")
            expected_authorities = _authority_results(
                contract, producer_by_id, outcome_by_id
            )
            if report["authorities"] != expected_authorities:
                errors.append("core principles authority consumers are stale or inconsistent")
        authority_by_id = {
            item.get("id"): item
            for item in report["authorities"]
            if isinstance(item, dict)
        }
        for authority in contract.get("principle_acceptance_contract", {}).get("authorities", []):
            saved = authority_by_id.get(authority.get("id"))
            value = resolve_json_pointer(contract, authority["pointer"])
            if not isinstance(saved, dict) or saved.get("value_sha256") != _sha256_bytes(_canonical_json(value)):
                errors.append(f"core principles authority hash is stale: {authority.get('id')}")
    return errors[:MAX_SAVED_REPORT_SCHEMA_ERRORS]


def _args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gate",
        choices=("authoring", "formal-release"),
        default="authoring",
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _args(sys.argv[1:] if argv is None else argv)
    root = args.root.resolve()
    contract_path = root / CANONICAL_CONTRACT_SOURCE
    try:
        contract_bytes = contract_path.read_bytes()
        contract = json.loads(contract_bytes)
        if not isinstance(contract, dict):
            raise ValueError("Core Model root must be an object")
        contract_sha256 = _sha256_bytes(contract_bytes)
        report = evaluate(
            root,
            contract,
            contract_sha256=contract_sha256,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        report = _invalid_report(root, None, [str(exc)])
    write_reports(root, report)
    selected_gate_status = (
        report["authoring_principles_status"]
        if args.gate == "authoring"
        else report["formal_principles_status"]
    )
    print(
        "eval-core-principles: "
        f"authoring_principles={report['authoring_principles_status']}; "
        f"formal_principles={report['formal_principles_status']}; "
        f"selected_gate={args.gate}:{selected_gate_status}; "
        f"commands={report['command_execution_count']}"
    )
    if selected_gate_status != "pass":
        for producer in report["producers"]:
            if producer["status"] == "pass":
                continue
            diagnostic = {
                "id": producer["id"],
                "status": producer["status"],
                "exit_code": producer["exit_code"],
                "timed_out": producer["timed_out"],
                "failure_reason_codes": producer["failure_reason_codes"],
                "depends_on": producer["depends_on"],
            }
            print(
                "eval-core-principles: producer_nonpass="
                + json.dumps(diagnostic, separators=(",", ":")),
                file=sys.stderr,
            )
    if report["contract_errors"]:
        for error in report["contract_errors"][:10]:
            print(f"eval-core-principles: ERROR: {error}", file=sys.stderr)
    return 0 if selected_gate_status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
