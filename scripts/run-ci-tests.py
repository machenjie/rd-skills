#!/usr/bin/env python3
"""Run the unit-test projection of the Core-owned Impact Graph."""

from __future__ import annotations

import argparse
import ast
import contextlib
from dataclasses import asdict, dataclass, replace
import io
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import IO, Iterator, Sequence

from impact_graph import ImpactGraphError, load_core, select


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JOBS = 2
DEFAULT_TIMEOUT_SECONDS = 900.0
FULL_DISCOVERY_TIMEOUT_SECONDS = 120.0
FULL_MAX_LOG_BYTES = 1024 * 1024
FULL_RESOURCE_DECLARATION = "FULL_TEST_RESOURCE_CLASS"
TEST_TIMEOUT_DECLARATION = "TEST_TIMEOUT_CLASS"
FULL_RESOURCE_WEIGHT_CAPACITY = 4
FULL_RESOURCE_PROFILES = {
    "standard": (1, False, False),
    "heavy": (3, True, False),
    "tokenizer": (1, False, True),
    "heavy-tokenizer": (3, True, True),
}
TEST_TIMEOUT_MULTIPLIERS = {
    "standard": 1.0,
    "source-validation": 2.0,
}
POLL_SECONDS = 0.01
TERMINATE_GRACE_SECONDS = 1.0
INTERNAL_DISCOVERY_ACTION = "_discover-full-manifest"
INTERNAL_CHILD_BOOTSTRAP_ACTION = "_exec-python-child"
RUNNER_SIGNALS = (signal.SIGINT, signal.SIGTERM)
_FULL_SIGNAL_OWNED = False
_FULL_EXIT_CODE_FINALIZED = False
_FULL_INTERRUPT_OBSERVED = False


class SelectionError(RuntimeError):
    """The selected unit-test target set cannot be executed safely."""


class RunnerInterrupted(RuntimeError):
    """The runner received an interrupt while workers were active."""


class OutputLimitExceeded(RuntimeError):
    """A bounded stdout or stderr sink rejected additional bytes."""


@dataclass
class FullDiscoveryManifest:
    """A no-test-execution manifest derived from unittest discovery."""

    modules: list[str]
    test_ids: list[str]
    exclusive_modules: list[str]
    resource_classes: dict[str, str]


@dataclass
class WorkerResult:
    """One isolated module result retained after its temporary files are removed."""

    module: str
    status: str
    exit_code: int | None
    timed_out: bool
    duration_seconds: float
    stdout: str
    stderr: str
    detail: str
    pid: int | None
    tmpdir: str | None


@dataclass
class WorkerHandle:
    """Live worker resources owned exclusively by the affected-test runner."""

    module: str
    process: subprocess.Popen[bytes]
    temporary: tempfile.TemporaryDirectory[str]
    stdout_path: Path
    stderr_path: Path
    stdout_stream: IO[bytes] | None
    stderr_stream: IO[bytes] | None
    started_at: float
    timeout_seconds: float
    max_log_bytes: int | None = None
    process_group_id: int | None = None
    owns_process_group: bool = False
    stdout_capture: BoundedPipeCapture | None = None
    stderr_capture: BoundedPipeCapture | None = None


class BoundedPipeCapture:
    """Drain one binary pipe concurrently while retaining at most a fixed prefix."""

    def __init__(self, label: str, stream: IO[bytes], max_bytes: int) -> None:
        if max_bytes < 1:
            raise ValueError("bounded pipe size must be positive")
        self.label = label
        self.stream = stream
        self.max_bytes = max_bytes
        self._buffer = bytearray()
        self.exceeded = threading.Event()
        self.completed = threading.Event()
        self.error: OSError | None = None
        self.started = False
        self.thread = threading.Thread(
            target=self._drain,
            name=f"changeforge-{label}-drain",
            daemon=True,
        )

    def start(self) -> None:
        self.thread.start()
        self.started = True

    def _drain(self) -> None:
        try:
            while True:
                chunk = self.stream.read(8192)
                if not chunk:
                    break
                remaining = self.max_bytes - len(self._buffer)
                if remaining > 0:
                    self._buffer.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    self.exceeded.set()
        except OSError as exc:
            self.error = exc
        finally:
            try:
                self.stream.close()
            except OSError as exc:
                self.error = self.error or exc
            self.completed.set()

    def finish(self) -> tuple[bytes, list[str]]:
        if not self.started:
            return bytes(self._buffer), []
        self.thread.join(timeout=TERMINATE_GRACE_SECONDS)
        errors: list[str] = []
        if self.thread.is_alive():
            errors.append(f"{self.label} drain did not finish")
        if self.error is not None:
            errors.append(f"{self.label} drain failed: {self.error}")
        if self.exceeded.is_set():
            errors.append(
                f"{self.label} exceeded {self.max_bytes} bytes and was truncated"
            )
        return bytes(self._buffer), errors


class BoundedTextCapture(io.TextIOBase):
    """A UTF-8 text sink that fails on the first byte beyond its retained cap."""

    def __init__(self, label: str, max_bytes: int) -> None:
        super().__init__()
        if max_bytes < 1:
            raise ValueError("bounded text size must be positive")
        self.label = label
        self.max_bytes = max_bytes
        self._buffer = bytearray()

    @property
    def encoding(self) -> str:
        return "utf-8"

    def writable(self) -> bool:
        return True

    def write(self, text: str) -> int:
        if not isinstance(text, str):
            raise TypeError("bounded text capture accepts strings")
        encoded = text.encode("utf-8")
        remaining = self.max_bytes - len(self._buffer)
        if len(encoded) > remaining:
            if remaining > 0:
                self._buffer.extend(encoded[:remaining])
            raise OutputLimitExceeded(
                f"{self.label} output exceeded {self.max_bytes} bytes"
            )
        self._buffer.extend(encoded)
        return len(text)

    def getvalue(self) -> str:
        return bytes(self._buffer).decode("utf-8", errors="replace")


def _selection(
    root: Path,
    core: dict,
    base_sha: str | None,
    head_sha: str | None,
) -> dict:
    return select(root, core, base_sha, head_sha)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be finite and greater than 0")
    return parsed


def _isolated_python_environment(root: Path, temporary: str) -> dict[str, str]:
    """Return one trusted Python import environment for every child process."""

    resolved_root = root.resolve()
    import_roots = tuple(
        dict.fromkeys(
            (
                resolved_root,
                resolved_root / "scripts",
                Path(__file__).resolve().parent,
            )
        )
    )
    if any(os.pathsep in str(path) for path in import_roots):
        raise SelectionError(
            "repository import paths cannot contain the platform path separator"
        )
    environment = os.environ.copy()
    environment.pop("PYTHONSAFEPATH", None)
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHONPATH": os.pathsep.join(str(path) for path in import_roots),
            "TMPDIR": temporary,
            "TMP": temporary,
            "TEMP": temporary,
        }
    )
    return environment


def _supports_child_signal_bootstrap() -> bool:
    return os.name == "posix" and callable(
        getattr(signal, "pthread_sigmask", None)
    )


def _python_child_command(*arguments: str) -> list[str]:
    """Use the signal bootstrap only where its POSIX primitive is supported."""

    if not _supports_child_signal_bootstrap():
        return [sys.executable, "-P", *arguments]

    return [
        sys.executable,
        "-P",
        str(Path(__file__).resolve()),
        INTERNAL_CHILD_BOOTSTRAP_ACTION,
        *arguments,
    ]


def _internal_child_bootstrap_main(arguments: Sequence[str]) -> int:
    """Unblock only runner-owned signals, then replace this process with Python."""

    if not arguments:
        print("internal Python child command is empty", file=sys.stderr)
        return 2
    if not _supports_child_signal_bootstrap():
        print("internal Python child signal bootstrap is unavailable", file=sys.stderr)
        return 2
    signal.pthread_sigmask(signal.SIG_UNBLOCK, RUNNER_SIGNALS)
    try:
        os.execv(sys.executable, [sys.executable, "-P", *arguments])
    except OSError as exc:
        print(f"internal Python child exec failed: {exc}", file=sys.stderr)
        return 2


def _raise_runner_interrupted(signum: int, _frame: object) -> None:
    raise RunnerInterrupted(f"received signal {signum}")


def _raise_full_runner_interrupted(signum: int, _frame: object) -> None:
    global _FULL_INTERRUPT_OBSERVED
    if _FULL_EXIT_CODE_FINALIZED or _FULL_INTERRUPT_OBSERVED:
        raise SystemExit(2)
    _FULL_INTERRUPT_OBSERVED = True
    raise RunnerInterrupted(f"received signal {signum}")


def _supports_atomic_interrupt_lifecycle() -> bool:
    return (
        os.name == "posix"
        and threading.current_thread() is threading.main_thread()
        and all(
            hasattr(signal, name)
            for name in ("pthread_sigmask", "sigpending", "sigwait")
        )
    )


def _consume_pending_runner_signals() -> tuple[int, ...]:
    """Consume owned signals while they are blocked, before changing the mask."""

    pending = sorted(set(signal.sigpending()).intersection(RUNNER_SIGNALS))
    consumed: list[int] = []
    for signal_number in pending:
        consumed.append(signal.sigwait({signal_number}))
    return tuple(consumed)


def _restore_interrupt_handlers(
    previous_handlers: dict[int, object],
) -> list[BaseException]:
    """Attempt every restoration and retry transient failures once."""

    remaining = dict(previous_handlers)
    errors: list[BaseException] = []
    for _attempt in range(2):
        if not remaining:
            break
        failed: dict[int, object] = {}
        for signal_number, previous in remaining.items():
            try:
                signal.signal(signal_number, previous)
            except BaseException as exc:
                errors.append(exc)
                failed[signal_number] = previous
        remaining = failed
    if not remaining:
        return []
    return errors


def _acquire_full_interrupt_ownership() -> None:
    """Own runner signals until process exit; never restore them in Python."""

    global _FULL_INTERRUPT_OBSERVED, _FULL_SIGNAL_OWNED
    if not _supports_atomic_interrupt_lifecycle():
        raise SelectionError(
            "full regression runner requires a POSIX atomic signal lifecycle"
        )
    if _FULL_SIGNAL_OWNED:
        raise SelectionError("full regression signal ownership is process-lifetime")

    owned_signals = set(RUNNER_SIGNALS)
    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, owned_signals)
    installed: set[int] = set()
    try:
        for signal_number in RUNNER_SIGNALS:
            signal.signal(signal_number, _raise_full_runner_interrupted)
            installed.add(signal_number)
    except BaseException as exc:
        # Full runs only as an isolated CLI process. Keep signals blocked when
        # complete ownership cannot be established and fail before discovery.
        raise SelectionError(
            "full regression signal ownership could not be established for "
            f"{sorted(owned_signals - installed)}"
        ) from exc

    _FULL_SIGNAL_OWNED = True
    pending = _consume_pending_runner_signals()
    signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    if pending:
        _FULL_INTERRUPT_OBSERVED = True
        raise RunnerInterrupted(
            "received signal during full interrupt handler installation"
        )


def _finalize_full_exit_code(exit_code: int) -> int:
    """Irrevocably select the Full CLI exit code before its final unmask."""

    global _FULL_EXIT_CODE_FINALIZED, _FULL_INTERRUPT_OBSERVED
    if not _FULL_SIGNAL_OWNED:
        return 2
    owned_signals = set(RUNNER_SIGNALS)
    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, owned_signals)
    pending = _consume_pending_runner_signals()
    if pending:
        _FULL_INTERRUPT_OBSERVED = True
    _FULL_EXIT_CODE_FINALIZED = True
    signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    return 2 if _FULL_INTERRUPT_OBSERVED else exit_code


@contextlib.contextmanager
def _interrupt_lifecycle(*, enabled: bool) -> Iterator[None]:
    """Install and restore handlers as one exception-safe ownership scope."""

    if not enabled:
        yield
        return
    if _supports_atomic_interrupt_lifecycle():
        owned_signals = set(RUNNER_SIGNALS)
        previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, owned_signals)
        previous_handlers: dict[int, object] = {}
        try:
            for signal_number in RUNNER_SIGNALS:
                previous_handlers[signal_number] = signal.signal(
                    signal_number, _raise_runner_interrupted
                )
        except BaseException as install_error:
            restoration_errors = _restore_interrupt_handlers(previous_handlers)
            pending_error: BaseException | None = None
            try:
                _consume_pending_runner_signals()
            except BaseException as exc:
                pending_error = exc
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            if restoration_errors:
                raise RunnerInterrupted(
                    "interrupt handler installation failed and restoration "
                    "could not be proven"
                ) from install_error
            if pending_error is not None:
                raise RunnerInterrupted(
                    "interrupt handler installation failed and pending-signal "
                    "cleanup could not be proven"
                ) from pending_error
            raise

        installation_signals = _consume_pending_runner_signals()
        try:
            signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            if installation_signals:
                raise RunnerInterrupted(
                    "received signal during interrupt handler installation"
                )
            yield
        finally:
            restoration_mask = signal.pthread_sigmask(
                signal.SIG_BLOCK, owned_signals
            )
            restoration_errors = _restore_interrupt_handlers(previous_handlers)
            restoration_signals: tuple[int, ...] = ()
            pending_error: BaseException | None = None
            try:
                restoration_signals = _consume_pending_runner_signals()
            except BaseException as exc:
                pending_error = exc
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, restoration_mask)
            if restoration_errors:
                raise RunnerInterrupted(
                    "interrupt handler restoration could not be proven"
                )
            if pending_error is not None:
                raise RunnerInterrupted(
                    "pending-signal cleanup during handler restoration could not be proven"
                ) from pending_error
            if restoration_signals:
                raise RunnerInterrupted(
                    "received signal during interrupt handler restoration"
                )
        return

    # Ordinary affected execution retains its best-effort behavior on platforms
    # without the POSIX primitives required by the Full regression action.
    previous_handlers: dict[int, object] = {}
    try:
        for signal_number in RUNNER_SIGNALS:
            try:
                previous_handlers[signal_number] = signal.signal(
                    signal_number, _raise_runner_interrupted
                )
            except (ValueError, OSError):
                continue
        yield
    finally:
        for signal_number, previous in previous_handlers.items():
            signal.signal(signal_number, previous)


@contextlib.contextmanager
def _blocked_runner_signals() -> Iterator[None]:
    if os.name != "posix" or not hasattr(signal, "pthread_sigmask"):
        yield
        return
    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, RUNNER_SIGNALS)
    try:
        yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)


def _supports_owned_process_groups() -> bool:
    return os.name == "posix" and hasattr(os, "killpg")


def _process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_for_process_group_exit(
    process: subprocess.Popen[bytes],
    process_group_id: int,
    timeout_seconds: float,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while _process_group_exists(process_group_id):
        process.poll()
        if time.monotonic() >= deadline:
            return False
        time.sleep(POLL_SECONDS)
    return True


def _terminate_process_tree(
    process: subprocess.Popen[bytes], process_group_id: int | None
) -> bool:
    """Terminate only the dedicated child group, then wait for it to disappear."""

    if process_group_id is not None and _supports_owned_process_groups():
        if _process_group_exists(process_group_id):
            try:
                os.killpg(process_group_id, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except OSError:
                return False
        if not _wait_for_process_group_exit(
            process, process_group_id, TERMINATE_GRACE_SECONDS
        ):
            try:
                os.killpg(process_group_id, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError:
                return False
            if not _wait_for_process_group_exit(
                process, process_group_id, TERMINATE_GRACE_SECONDS
            ):
                return False
        try:
            process.wait(timeout=TERMINATE_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            return False
        return process.poll() is not None

    if process.poll() is not None:
        return True
    try:
        process.terminate()
        process.wait(timeout=TERMINATE_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=TERMINATE_GRACE_SECONDS)
        except (OSError, subprocess.TimeoutExpired):
            return False
    except OSError:
        if process.poll() is None:
            return False
    return process.poll() is not None


def _start_worker(
    root: Path,
    module: str,
    timeout_seconds: float,
    *,
    max_log_bytes: int | None = None,
    owns_process_group: bool = False,
    startup_slot: list[WorkerHandle] | None = None,
) -> WorkerHandle:
    if max_log_bytes is not None and max_log_bytes < 1:
        raise ValueError("worker log size must be positive")
    if owns_process_group and not _supports_owned_process_groups():
        raise SelectionError(
            "full regression runner requires POSIX process-group cleanup"
        )
    temporary = tempfile.TemporaryDirectory(prefix="changeforge-ci-test-")
    temp_path = Path(temporary.name)
    stdout_path = temp_path / "stdout.log"
    stderr_path = temp_path / "stderr.log"
    stdout_stream: IO[bytes] | None = None
    stderr_stream: IO[bytes] | None = None
    stdout_capture: BoundedPipeCapture | None = None
    stderr_capture: BoundedPipeCapture | None = None
    process: subprocess.Popen[bytes] | None = None
    process_group_id: int | None = None
    handle: WorkerHandle | None = None
    try:
        if max_log_bytes is None:
            stdout_stream = stdout_path.open("wb")
            stderr_stream = stderr_path.open("wb")
        environment = _isolated_python_environment(root, temporary.name)
        popen_options: dict[str, object] = {}
        if os.name == "posix":
            popen_options["start_new_session"] = True
        elif os.name == "nt":
            popen_options["creationflags"] = getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0
            )
        process = subprocess.Popen(
            _python_child_command("-m", "unittest", module),
            cwd=root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE if max_log_bytes is not None else stdout_stream,
            stderr=subprocess.PIPE if max_log_bytes is not None else stderr_stream,
            **popen_options,
        )
        if os.name == "posix":
            process_group_id = process.pid
        if max_log_bytes is not None:
            if process.stdout is None or process.stderr is None:
                raise OSError("worker pipe capture was not created")
            stdout_capture = BoundedPipeCapture(
                "stdout", process.stdout, max_log_bytes
            )
            stderr_capture = BoundedPipeCapture(
                "stderr", process.stderr, max_log_bytes
            )
            stdout_capture.start()
            stderr_capture.start()
        handle = WorkerHandle(
            module=module,
            process=process,
            temporary=temporary,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            stdout_stream=stdout_stream,
            stderr_stream=stderr_stream,
            started_at=time.monotonic(),
            timeout_seconds=timeout_seconds,
            max_log_bytes=max_log_bytes,
            process_group_id=process_group_id,
            owns_process_group=owns_process_group,
            stdout_capture=stdout_capture,
            stderr_capture=stderr_capture,
        )
        if startup_slot is not None:
            startup_slot.append(handle)
        return handle
    except BaseException:
        if (
            handle is not None
            and startup_slot is not None
            and startup_slot
            and startup_slot[-1] is handle
        ):
            raise
        if process is not None:
            _terminate_process_tree(process, process_group_id)
        if stdout_stream is not None:
            stdout_stream.close()
        if stderr_stream is not None:
            stderr_stream.close()
        temporary.cleanup()
        raise


def _terminate_worker(handle: WorkerHandle) -> bool:
    return _terminate_process_tree(handle.process, handle.process_group_id)


def _finish_worker(
    handle: WorkerHandle,
    *,
    forced_status: str | None = None,
    timed_out: bool = False,
    detail: str = "",
) -> WorkerResult:
    duration = max(0.0, time.monotonic() - handle.started_at)
    resource_errors: list[str] = []
    captured: dict[str, str] = {}

    def read_log(label: str, path: Path, stream: IO[bytes] | None) -> str:
        if stream is None:
            resource_errors.append(f"{label} stream is unavailable")
            return ""
        try:
            stream.close()
        except OSError as exc:
            resource_errors.append(f"{label} close failed: {exc}")
        try:
            raw = path.read_bytes()
            return raw.decode("utf-8", errors="replace")
        except OSError as exc:
            resource_errors.append(f"{label} read failed: {exc}")
            return ""

    for label, capture, path, stream in (
        (
            "stdout",
            handle.stdout_capture,
            handle.stdout_path,
            handle.stdout_stream,
        ),
        (
            "stderr",
            handle.stderr_capture,
            handle.stderr_path,
            handle.stderr_stream,
        ),
    ):
        if capture is None:
            captured[label] = read_log(label, path, stream)
            continue
        raw, capture_errors = capture.finish()
        resource_errors.extend(capture_errors)
        captured[label] = raw.decode("utf-8", errors="replace")

    stdout = captured["stdout"]
    stderr = captured["stderr"]
    exit_code = handle.process.poll()
    status = forced_status
    if status is None:
        if exit_code == 0:
            status = "pass"
        elif exit_code == 1:
            status = "fail"
        else:
            status = "error"
            detail = detail or f"worker exited with unexpected code {exit_code}"
    try:
        handle.temporary.cleanup()
    except OSError as exc:
        resource_errors.append(f"temporary cleanup failed: {exc}")
    if resource_errors:
        detail = "; ".join(item for item in (detail, *resource_errors) if item)
        status = "error"
    return WorkerResult(
        module=handle.module,
        status=status,
        exit_code=exit_code,
        timed_out=timed_out,
        duration_seconds=round(duration, 6),
        stdout=stdout,
        stderr=stderr,
        detail=detail,
        pid=handle.process.pid,
        tmpdir=handle.temporary.name,
    )


def _poll_workers(active: dict[str, WorkerHandle]) -> list[WorkerResult]:
    completed: list[WorkerResult] = []
    now = time.monotonic()
    for module in sorted(active):
        handle = active[module]
        oversized = any(
            capture is not None and capture.exceeded.is_set()
            for capture in (handle.stdout_capture, handle.stderr_capture)
        )
        if oversized:
            cleaned = _terminate_worker(handle)
            completed.append(
                _finish_worker(
                    handle,
                    forced_status="error",
                    detail=(
                        f"worker log exceeded {handle.max_log_bytes} bytes"
                        if cleaned
                        else "worker log limit was exceeded and process cleanup could not be proven"
                    ),
                )
            )
            continue
        return_code = handle.process.poll()
        if return_code is not None:
            if (
                handle.owns_process_group
                and handle.process_group_id is not None
                and _process_group_exists(handle.process_group_id)
            ):
                cleaned = _terminate_worker(handle)
                completed.append(
                    _finish_worker(
                        handle,
                        forced_status="error",
                        detail=(
                            "worker descendant remained after leader exit and was terminated"
                            if cleaned
                            else "worker leader exited but descendant cleanup could not be proven"
                        ),
                    )
                )
                continue
            completed.append(_finish_worker(handle))
            continue
        if now - handle.started_at >= handle.timeout_seconds:
            cleaned = _terminate_worker(handle)
            completed.append(
                _finish_worker(
                    handle,
                    forced_status="timeout" if cleaned else "error",
                    timed_out=True,
                    detail=(
                        f"worker exceeded {handle.timeout_seconds:g}s"
                        if cleaned
                        else "worker timed out and process cleanup could not be proven"
                    ),
                )
            )
    for result in completed:
        active.pop(result.module)
    return completed


def _not_run_result(module: str, detail: str) -> WorkerResult:
    return WorkerResult(
        module=module,
        status="not-run",
        exit_code=None,
        timed_out=False,
        duration_seconds=0.0,
        stdout="",
        stderr="",
        detail=detail,
        pid=None,
        tmpdir=None,
    )


def _interrupted_module_results(
    modules: Sequence[str],
    completed: Sequence[WorkerResult],
    detail: str,
) -> list[WorkerResult]:
    """Complete a module manifest with one deterministic interruption signal."""

    by_module = {result.module: result for result in completed}
    missing = sorted(set(modules) - set(by_module))
    if missing:
        interrupted_module = missing[0]
        by_module[interrupted_module] = WorkerResult(
            module=interrupted_module,
            status="interrupted",
            exit_code=None,
            timed_out=False,
            duration_seconds=0.0,
            stdout="",
            stderr="",
            detail=detail,
            pid=None,
            tmpdir=None,
        )
        for module in missing[1:]:
            by_module[module] = _not_run_result(module, detail)
    elif by_module:
        interrupted_module = sorted(by_module)[-1]
        by_module[interrupted_module] = replace(
            by_module[interrupted_module], status="interrupted", detail=detail
        )
    return [by_module[module] for module in sorted(by_module)]


def _validate_full_resource_classes(
    modules: Sequence[str], resource_classes: dict[str, str]
) -> None:
    module_set = set(modules)
    if set(resource_classes) != module_set:
        missing = sorted(module_set - set(resource_classes))
        extra = sorted(set(resource_classes) - module_set)
        raise SelectionError(
            "full unittest resource class map must exactly cover modules: "
            f"missing={missing}, extra={extra}"
        )
    unknown = sorted(
        {
            resource_class
            for resource_class in resource_classes.values()
            if resource_class not in FULL_RESOURCE_PROFILES
        }
    )
    if unknown:
        raise SelectionError(f"unknown full unittest resource classes: {unknown}")


def _ordered_full_modules(
    modules: Sequence[str], resource_classes: dict[str, str]
) -> list[str]:
    """Order the weighted Full critical path before deterministic path ties."""

    _validate_full_resource_classes(modules, resource_classes)
    return sorted(
        modules,
        key=lambda module: (
            -FULL_RESOURCE_PROFILES[resource_classes[module]][0],
            module,
        ),
    )


def _first_full_dispatch_candidate(
    pending: Sequence[str],
    active_modules: Sequence[str],
    resource_classes: dict[str, str],
    *,
    jobs: int,
) -> str | None:
    """Return the first queued module that fits every Full safe-lane limit."""

    if len(active_modules) >= jobs:
        return None
    active_profiles = [
        FULL_RESOURCE_PROFILES[resource_classes[module]] for module in active_modules
    ]
    active_weight = sum(profile[0] for profile in active_profiles)
    heavy_active = any(profile[1] for profile in active_profiles)
    tokenizer_active = any(profile[2] for profile in active_profiles)
    for module in pending:
        weight, heavy, tokenizer = FULL_RESOURCE_PROFILES[resource_classes[module]]
        if active_weight + weight > FULL_RESOURCE_WEIGHT_CAPACITY:
            continue
        if heavy and heavy_active:
            continue
        if tokenizer and tokenizer_active:
            continue
        return module
    return None


def _execute_modules(
    root: Path,
    modules: Sequence[str],
    *,
    jobs: int,
    timeout_seconds: float,
    max_log_bytes: int | None = None,
    owns_process_group: bool = False,
    manage_interrupts: bool = True,
    resource_classes: dict[str, str] | None = None,
) -> list[WorkerResult]:
    if not modules or len(modules) != len(set(modules)):
        raise SelectionError("unittest selection must be non-empty and duplicate-free")
    if jobs < 1 or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise SelectionError(
            "jobs must be positive and timeout must be positive and finite"
        )

    if resource_classes is None:
        pending = list(modules)
    else:
        pending = _ordered_full_modules(modules, resource_classes)
    active: dict[str, WorkerHandle] = {}
    results: dict[str, WorkerResult] = {}
    stop_dispatch = False
    interrupted = False
    starting_module: str | None = None
    startup_slot: list[WorkerHandle] = []
    try:
        try:
            with _interrupt_lifecycle(enabled=manage_interrupts):
                while pending or active:
                    while pending and not stop_dispatch:
                        if resource_classes is None:
                            module = pending[0] if len(active) < jobs else None
                        else:
                            module = _first_full_dispatch_candidate(
                                pending,
                                list(active),
                                resource_classes,
                                jobs=jobs,
                            )
                        if module is None:
                            break
                        starting_module = module
                        startup_slot.clear()
                        try:
                            with _blocked_runner_signals():
                                if max_log_bytes is None:
                                    handle = _start_worker(
                                        root,
                                        module,
                                        _test_timeout_seconds(
                                            root, module, timeout_seconds
                                        ),
                                        startup_slot=startup_slot,
                                    )
                                else:
                                    handle = _start_worker(
                                        root,
                                        module,
                                        _test_timeout_seconds(
                                            root, module, timeout_seconds
                                        ),
                                        max_log_bytes=max_log_bytes,
                                        owns_process_group=owns_process_group,
                                        startup_slot=startup_slot,
                                    )
                                active[module] = handle
                                pending.remove(module)
                                startup_slot.clear()
                                starting_module = None
                        except OSError as exc:
                            pending.remove(module)
                            results[module] = WorkerResult(
                                module=module,
                                status="error",
                                exit_code=None,
                                timed_out=False,
                                duration_seconds=0.0,
                                stdout="",
                                stderr="",
                                detail=f"worker start failed: {exc}",
                                pid=None,
                                tmpdir=None,
                            )
                            starting_module = None
                            startup_slot.clear()
                            stop_dispatch = True
                    if not active:
                        break
                    completed = _poll_workers(active)
                    for result in completed:
                        results[result.module] = result
                        if result.status != "pass":
                            stop_dispatch = True
                    if active and not completed:
                        time.sleep(POLL_SECONDS)
        except (KeyboardInterrupt, RunnerInterrupted):
            interrupted = True
            stop_dispatch = True
            if starting_module is not None:
                module = starting_module
                handle = startup_slot[-1] if startup_slot else None
                if handle is not None and active.get(module) is handle:
                    active.pop(module)
                if module in pending:
                    pending.remove(module)
                if handle is None:
                    results[module] = WorkerResult(
                        module=module,
                        status="interrupted",
                        exit_code=None,
                        timed_out=False,
                        duration_seconds=0.0,
                        stdout="",
                        stderr="",
                        detail="worker start interrupted before registration",
                        pid=None,
                        tmpdir=None,
                    )
                else:
                    cleaned = _terminate_worker(handle)
                    results[module] = _finish_worker(
                        handle,
                        forced_status="interrupted" if cleaned else "error",
                        detail=(
                            "worker start interrupted and process was cleaned"
                            if cleaned
                            else "worker start interrupted and process cleanup could not be proven"
                        ),
                    )
                starting_module = None
                startup_slot.clear()
            elif pending and not active:
                module = pending.pop(0)
                results[module] = WorkerResult(
                    module=module,
                    status="interrupted",
                    exit_code=None,
                    timed_out=False,
                    duration_seconds=0.0,
                    stdout="",
                    stderr="",
                    detail="runner interrupted before worker start",
                    pid=None,
                    tmpdir=None,
                )
            for module, handle in list(active.items()):
                cleaned = _terminate_worker(handle)
                results[module] = _finish_worker(
                    handle,
                    forced_status="interrupted" if cleaned else "error",
                    detail=(
                        "runner interrupted"
                        if cleaned
                        else "runner interrupted and process cleanup could not be proven"
                    ),
                )
                active.pop(module)
    finally:
        for module, handle in list(active.items()):
            cleaned = _terminate_worker(handle)
            results[module] = _finish_worker(
                handle,
                forced_status="interrupted" if cleaned else "error",
                detail=(
                    "runner stopped before worker completion"
                    if cleaned
                    else "runner stopped and process cleanup could not be proven"
                ),
            )
            active.pop(module)

    if interrupted and not any(
        result.status in {"error", "interrupted"} for result in results.values()
    ):
        results = {
            result.module: result
            for result in _interrupted_module_results(
                modules,
                list(results.values()),
                "runner interrupted during handler restoration",
            )
        }
    reason = "runner interrupted" if interrupted else "dispatch stopped after failure"
    for module in pending:
        results.setdefault(module, _not_run_result(module, reason))
    return [results[module] for module in sorted(results)]


def _execute_full_modules(
    root: Path,
    modules: Sequence[str],
    *,
    exclusive_modules: Sequence[str],
    jobs: int,
    timeout_seconds: float,
    resource_classes: dict[str, str] | None = None,
) -> list[WorkerResult]:
    """Run safe modules concurrently, then the exclusive lane with no overlap."""

    if not _supports_owned_process_groups():
        raise SelectionError(
            "full regression runner requires POSIX process-group cleanup"
        )
    if not _supports_atomic_interrupt_lifecycle():
        raise SelectionError(
            "full regression runner requires a POSIX atomic signal lifecycle"
        )
    if not modules or len(modules) != len(set(modules)):
        raise SelectionError("full unittest modules must be non-empty and duplicate-free")
    if len(exclusive_modules) != len(set(exclusive_modules)):
        raise SelectionError("exclusive unittest modules must be duplicate-free")
    unknown = sorted(set(exclusive_modules) - set(modules))
    if unknown:
        raise SelectionError(f"exclusive unittest modules are not discovered: {unknown}")
    full_resource_classes = (
        {module: "standard" for module in modules}
        if resource_classes is None
        else resource_classes
    )
    _validate_full_resource_classes(modules, full_resource_classes)

    exclusive_set = set(exclusive_modules)
    safe = sorted(module for module in modules if module not in exclusive_set)
    safe_resource_classes = {
        module: full_resource_classes[module] for module in safe
    }
    exclusive = sorted(exclusive_set)
    results: list[WorkerResult] = []
    try:
        if safe:
            results.extend(
                _execute_modules(
                    root,
                    safe,
                    jobs=jobs,
                    timeout_seconds=timeout_seconds,
                    max_log_bytes=FULL_MAX_LOG_BYTES,
                    owns_process_group=True,
                    manage_interrupts=False,
                    resource_classes=safe_resource_classes,
                )
            )
        if any(result.status != "pass" for result in results):
            results.extend(
                _not_run_result(module, "exclusive lane not started after failure")
                for module in exclusive
            )
        elif exclusive:
            results.extend(
                _execute_modules(
                    root,
                    exclusive,
                    jobs=1,
                    timeout_seconds=timeout_seconds,
                    max_log_bytes=FULL_MAX_LOG_BYTES,
                    owns_process_group=True,
                    manage_interrupts=False,
                )
            )
    except (KeyboardInterrupt, RunnerInterrupted):
        return _interrupted_module_results(
            modules, results, "full unittest runner interrupted between lanes"
        )
    return sorted(results, key=lambda result: result.module)


def _parse_test_module(path: Path) -> ast.Module:
    try:
        source = path.read_text(encoding="utf-8")
        return ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise SelectionError(f"cannot classify unittest module {path}: {exc}") from exc


def _binding_targets(node: ast.AST) -> tuple[ast.AST, ...]:
    if isinstance(node, ast.Assign):
        return tuple(node.targets)
    if isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        return (node.target,)
    if isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
        return (node.target,)
    if isinstance(node, ast.withitem) and node.optional_vars is not None:
        return (node.optional_vars,)
    if hasattr(ast, "TypeAlias") and isinstance(node, ast.TypeAlias):
        return (node.name,)
    return ()


def _target_mentions_name(target: ast.AST, name: str) -> bool:
    return any(
        isinstance(candidate, ast.Name)
        and isinstance(candidate.ctx, ast.Store)
        and candidate.id == name
        for candidate in ast.walk(target)
    )


def _node_binds_name(node: ast.AST, name: str) -> bool:
    if any(
        _target_mentions_name(target, name) for target in _binding_targets(node)
    ):
        return True
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name == name
    if isinstance(node, ast.arg):
        return node.arg == name
    if isinstance(node, ast.Import):
        return any(
            (alias.asname or alias.name.split(".", 1)[0]) == name
            for alias in node.names
        )
    if isinstance(node, ast.ImportFrom):
        return any((alias.asname or alias.name) == name for alias in node.names)
    if isinstance(node, ast.ExceptHandler):
        return node.name == name
    if isinstance(node, (ast.MatchAs, ast.MatchStar)):
        return node.name == name
    if isinstance(node, ast.MatchMapping):
        return node.rest == name
    return False


def _literal_test_module_class(
    path: Path,
    *,
    declaration_name: str,
    allowed: set[str],
    default: str,
    label: str,
    tree: ast.Module | None = None,
) -> str:
    parsed = tree if tree is not None else _parse_test_module(path)
    declarations: list[ast.AST] = []
    top_level_ids = {id(statement) for statement in parsed.body}
    for node in ast.walk(parsed):
        if not _node_binds_name(node, declaration_name):
            continue
        declarations.append(node)
        if id(node) not in top_level_ids:
            raise SelectionError(
                f"{label} declaration must be top-level: {path}"
            )

    if not declarations:
        return default
    if len(declarations) != 1:
        raise SelectionError(f"duplicate {label} declarations: {path}")

    declaration = declarations[0]
    if isinstance(declaration, ast.Assign):
        valid_target = (
            len(declaration.targets) == 1
            and isinstance(declaration.targets[0], ast.Name)
            and declaration.targets[0].id == declaration_name
        )
        value = declaration.value
    elif isinstance(declaration, ast.AnnAssign):
        valid_target = (
            isinstance(declaration.target, ast.Name)
            and declaration.target.id == declaration_name
            and declaration.simple == 1
        )
        value = declaration.value
    else:
        valid_target = False
        value = None
    if (
        not valid_target
        or not isinstance(value, ast.Constant)
        or not isinstance(value.value, str)
    ):
        raise SelectionError(f"dynamic {label} declaration is forbidden: {path}")
    class_name = value.value
    if class_name not in allowed:
        raise SelectionError(f"unknown {label} {class_name!r}: {path}")
    return class_name


def _full_test_resource_class(path: Path, tree: ast.Module | None = None) -> str:
    """Read one optional source-owned literal resource declaration."""

    return _literal_test_module_class(
        path,
        declaration_name=FULL_RESOURCE_DECLARATION,
        allowed=set(FULL_RESOURCE_PROFILES),
        default="standard",
        label="full unittest resource class",
        tree=tree,
    )


def _test_timeout_class(path: Path, tree: ast.Module | None = None) -> str:
    """Read one optional closed timeout class without importing the test module."""

    return _literal_test_module_class(
        path,
        declaration_name=TEST_TIMEOUT_DECLARATION,
        allowed=set(TEST_TIMEOUT_MULTIPLIERS),
        default="standard",
        label="unittest timeout class",
        tree=tree,
    )


def _test_timeout_seconds(root: Path, module: str, base_seconds: float) -> float:
    path = root / module
    if not path.is_file():
        return base_seconds
    timeout_class = _test_timeout_class(path)
    return base_seconds * TEST_TIMEOUT_MULTIPLIERS[timeout_class]


def _node_mentions_root(node: ast.AST) -> bool:
    return any(
        (isinstance(candidate, ast.Name) and candidate.id == "ROOT")
        or (isinstance(candidate, ast.Attribute) and candidate.attr == "ROOT")
        for candidate in ast.walk(node)
    )


def _exclusive_lane_reason(
    path: Path, tree: ast.Module | None = None
) -> str | None:
    """Classify tests that mutate or directly execute against repository state."""

    parsed = tree if tree is not None else _parse_test_module(path)

    temporary_calls = {"TemporaryDirectory", "NamedTemporaryFile", "mkdtemp"}
    root_mutations = {
        "mkdir",
        "rename",
        "replace",
        "rmdir",
        "symlink_to",
        "touch",
        "unlink",
        "write_bytes",
        "write_text",
    }
    subprocess_calls = {"Popen", "call", "check_call", "check_output", "run"}
    for node in ast.walk(parsed):
        if not isinstance(node, ast.Call):
            continue
        function_name = (
            node.func.attr
            if isinstance(node.func, ast.Attribute)
            else node.func.id
            if isinstance(node.func, ast.Name)
            else ""
        )
        keywords = {item.arg: item.value for item in node.keywords if item.arg}
        if (
            function_name in temporary_calls
            and "dir" in keywords
            and _node_mentions_root(keywords["dir"])
        ):
            return "repository-root-temporary-state"
        if (
            function_name in root_mutations
            and isinstance(node.func, ast.Attribute)
            and _node_mentions_root(node.func.value)
        ):
            return "repository-root-mutation"
        if (
            function_name in subprocess_calls
            and "cwd" in keywords
            and _node_mentions_root(keywords["cwd"])
        ):
            return "repository-root-subprocess-or-inventory"
    return None


def _flatten_suite(suite: object) -> list[object]:
    import unittest

    if isinstance(suite, unittest.TestSuite):
        flattened: list[object] = []
        for child in suite:
            flattened.extend(_flatten_suite(child))
        return flattened
    return [suite]


def _internal_discovery_payload(
    root: Path, *, max_log_bytes: int
) -> dict[str, object]:
    """Import discovery targets and enumerate IDs without running test methods."""

    import contextlib
    import unittest

    tests_root = root / "tests"
    if not tests_root.is_dir():
        raise SelectionError(f"unittest start directory is missing: {tests_root}")
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    loader = unittest.TestLoader()
    captured_stdout = BoundedTextCapture(
        "full unittest discovery import stdout", max_log_bytes
    )
    captured_stderr = BoundedTextCapture(
        "full unittest discovery import stderr", max_log_bytes
    )
    with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(
        captured_stderr
    ):
        suite = loader.discover(str(tests_root), pattern="test*.py")
    if loader.errors:
        raise SelectionError("unittest discovery failed: " + " | ".join(loader.errors))

    test_ids = sorted(str(test.id()) for test in _flatten_suite(suite))
    if not test_ids:
        raise SelectionError("full unittest discovery selected no test IDs")
    if len(test_ids) != len(set(test_ids)):
        raise SelectionError("full unittest discovery returned duplicate test IDs")

    discovered_paths: set[Path] = set()
    resolved_tests = tests_root.resolve()
    for module in tuple(sys.modules.values()):
        raw_path = getattr(module, "__file__", None)
        if not isinstance(raw_path, str):
            continue
        path = Path(raw_path)
        if path.suffix in {".pyc", ".pyo"}:
            path = path.with_suffix(".py")
        try:
            resolved = path.resolve()
            resolved.relative_to(resolved_tests)
        except (OSError, ValueError):
            continue
        if resolved.name.startswith("test") and resolved.suffix == ".py":
            discovered_paths.add(resolved)
    modules = sorted(path.relative_to(root.resolve()).as_posix() for path in discovered_paths)
    if not modules or len(modules) != len(set(modules)):
        raise SelectionError("full unittest module discovery must be non-empty and duplicate-free")
    resource_classes: dict[str, str] = {}
    exclusive_modules: list[str] = []
    for path in sorted(discovered_paths):
        module = path.relative_to(root.resolve()).as_posix()
        tree = _parse_test_module(path)
        resource_classes[module] = _full_test_resource_class(path, tree)
        if _exclusive_lane_reason(path, tree) is not None:
            exclusive_modules.append(module)
    return {
        "modules": modules,
        "test_ids": test_ids,
        "exclusive_modules": exclusive_modules,
        "resource_classes": resource_classes,
    }


def _internal_discovery_main(root_arg: str, max_log_bytes_arg: str) -> int:
    try:
        max_log_bytes = int(max_log_bytes_arg)
        if max_log_bytes < 1:
            raise ValueError("full discovery log size must be positive")
        payload = _internal_discovery_payload(
            Path(root_arg).resolve(), max_log_bytes=max_log_bytes
        )
        print(json.dumps(payload, sort_keys=True))
        return 0
    except (OSError, OutputLimitExceeded, SelectionError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


def _discover_full_manifest(
    root: Path, *, timeout_seconds: float, manage_interrupts: bool = True
) -> FullDiscoveryManifest:
    """Obtain a hermetic discovery manifest in a bounded child process."""

    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise SelectionError("full discovery timeout must be positive and finite")
    if not _supports_owned_process_groups():
        raise SelectionError(
            "full regression discovery requires POSIX process-group cleanup"
        )
    if not _supports_atomic_interrupt_lifecycle():
        raise SelectionError(
            "full regression discovery requires a POSIX atomic signal lifecycle"
        )
    max_log_bytes = FULL_MAX_LOG_BYTES
    with tempfile.TemporaryDirectory(prefix="changeforge-full-discovery-") as temporary:
        process: subprocess.Popen[bytes] | None = None
        captures: list[BoundedPipeCapture] = []
        try:
            with _interrupt_lifecycle(enabled=manage_interrupts):
                try:
                    environment = _isolated_python_environment(root, temporary)
                    with _blocked_runner_signals():
                        process = subprocess.Popen(
                            _python_child_command(
                                str(Path(__file__).resolve()),
                                INTERNAL_DISCOVERY_ACTION,
                                str(root.resolve()),
                                str(max_log_bytes),
                            ),
                            cwd=root,
                            env=environment,
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            start_new_session=True,
                        )
                    if process.stdout is None or process.stderr is None:
                        raise SelectionError(
                            "full unittest discovery pipes were not created"
                        )
                    stdout_capture = BoundedPipeCapture(
                        "full unittest discovery stdout",
                        process.stdout,
                        max_log_bytes,
                    )
                    stderr_capture = BoundedPipeCapture(
                        "full unittest discovery stderr",
                        process.stderr,
                        max_log_bytes,
                    )
                    captures = [stdout_capture, stderr_capture]
                    stdout_capture.start()
                    stderr_capture.start()
                    deadline = time.monotonic() + timeout_seconds
                    while True:
                        if (
                            stdout_capture.exceeded.is_set()
                            or stderr_capture.exceeded.is_set()
                        ):
                            raise SelectionError(
                                "full unittest discovery output exceeded "
                                f"{max_log_bytes} bytes"
                            )
                        return_code = process.poll()
                        if return_code is not None:
                            if _process_group_exists(process.pid):
                                raise SelectionError(
                                    "full unittest discovery left a descendant process"
                                )
                            break
                        if time.monotonic() >= deadline:
                            raise SelectionError(
                                "full unittest discovery exceeded "
                                f"{timeout_seconds:g}s"
                            )
                        time.sleep(POLL_SECONDS)
                    stdout_raw, stdout_errors = stdout_capture.finish()
                    stderr_raw, stderr_errors = stderr_capture.finish()
                    capture_errors = [*stdout_errors, *stderr_errors]
                    if capture_errors:
                        raise SelectionError(
                            "full unittest discovery capture failed: "
                            + "; ".join(capture_errors)
                        )
                    stdout = stdout_raw.decode("utf-8", errors="replace")
                    stderr = stderr_raw.decode("utf-8", errors="replace")
                    if process.returncode != 0:
                        raise SelectionError(
                            "full unittest discovery subprocess failed: "
                            + (stderr.strip() or stdout.strip())
                        )
                except BaseException as exc:
                    cleanup_errors: list[str] = []
                    with _blocked_runner_signals():
                        if process is not None and not _terminate_process_tree(
                            process, process.pid
                        ):
                            cleanup_errors.append(
                                "owned process-group cleanup could not be proven"
                            )
                        for capture in captures:
                            _, capture_errors = capture.finish()
                            cleanup_errors.extend(
                                item
                                for item in capture_errors
                                if "did not finish" in item or "drain failed" in item
                            )
                    if isinstance(exc, (KeyboardInterrupt, RunnerInterrupted)):
                        detail = "full unittest discovery interrupted"
                    elif isinstance(exc, SelectionError):
                        detail = str(exc)
                    else:
                        detail = (
                            "full unittest discovery aborted: "
                            f"{type(exc).__name__}: {exc}"
                        )
                    if cleanup_errors:
                        detail += "; " + "; ".join(cleanup_errors)
                    raise SelectionError(detail) from exc
        except (KeyboardInterrupt, RunnerInterrupted) as exc:
            raise SelectionError("full unittest discovery interrupted") from exc
    try:
        payload = json.loads(stdout)
        manifest = FullDiscoveryManifest(
            modules=list(payload["modules"]),
            test_ids=list(payload["test_ids"]),
            exclusive_modules=list(payload["exclusive_modules"]),
            resource_classes=dict(payload["resource_classes"]),
        )
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise SelectionError("full unittest discovery returned malformed JSON") from exc
    if not all(isinstance(module, str) for module in manifest.modules):
        raise SelectionError("full unittest modules must be strings")
    if not all(isinstance(test_id, str) for test_id in manifest.test_ids):
        raise SelectionError("full unittest test IDs must be strings")
    if not all(
        isinstance(module, str) for module in manifest.exclusive_modules
    ):
        raise SelectionError("exclusive unittest modules must be strings")
    if not all(
        isinstance(module, str) and isinstance(resource_class, str)
        for module, resource_class in manifest.resource_classes.items()
    ):
        raise SelectionError("full unittest resource class map must use strings")
    if not manifest.modules or len(manifest.modules) != len(set(manifest.modules)):
        raise SelectionError("full unittest modules must be non-empty and duplicate-free")
    if not manifest.test_ids or len(manifest.test_ids) != len(set(manifest.test_ids)):
        raise SelectionError("full unittest test IDs must be non-empty and duplicate-free")
    if len(manifest.exclusive_modules) != len(set(manifest.exclusive_modules)):
        raise SelectionError("exclusive unittest modules must be duplicate-free")
    if not set(manifest.exclusive_modules).issubset(manifest.modules):
        raise SelectionError("exclusive unittest modules must be discovered modules")
    _validate_full_resource_classes(manifest.modules, manifest.resource_classes)
    root_resolved = root.resolve()
    for module in manifest.modules:
        path = Path(module)
        try:
            resolved = (root_resolved / path).resolve()
            resolved.relative_to(root_resolved / "tests")
        except (OSError, ValueError) as exc:
            raise SelectionError(
                f"full unittest module escapes the tests root: {module}"
            ) from exc
        if path.is_absolute() or not resolved.is_file():
            raise SelectionError(f"full unittest module is not a file: {module}")
    return manifest


def _exit_code(results: Sequence[WorkerResult]) -> int:
    if any(row.status in {"error", "timeout", "interrupted"} for row in results):
        return 2
    if any(row.status == "fail" for row in results):
        return 1
    return 0


def _print_results(results: Sequence[WorkerResult]) -> None:
    ordered = sorted(results, key=lambda result: result.module)
    print(
        json.dumps(
            {
                "worker_results": [asdict(result) for result in ordered],
            },
            sort_keys=True,
        ),
        flush=True,
    )


def _run_full_action(args: argparse.Namespace) -> int:
    """Run discovery, both execution lanes, and aggregation under one handler owner."""

    manifest: FullDiscoveryManifest | None = None
    results: list[WorkerResult] = []
    try:
        _acquire_full_interrupt_ownership()
        manifest = _discover_full_manifest(
            ROOT,
            timeout_seconds=FULL_DISCOVERY_TIMEOUT_SECONDS,
            manage_interrupts=False,
        )
        print(
            json.dumps(
                {
                    "reason": "full-regression",
                    "test_modules": manifest.modules,
                    "test_ids": manifest.test_ids,
                    "exclusive_test_modules": manifest.exclusive_modules,
                    "test_module_resource_classes": manifest.resource_classes,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if args.list_tests:
            return _finalize_full_exit_code(0)
        results = _execute_full_modules(
            ROOT,
            manifest.modules,
            exclusive_modules=manifest.exclusive_modules,
            jobs=args.jobs,
            timeout_seconds=args.timeout,
            resource_classes=manifest.resource_classes,
        )
        _print_results(results)
        return _finalize_full_exit_code(_exit_code(results))
    except (KeyboardInterrupt, RunnerInterrupted) as exc:
        if manifest is not None and not args.list_tests:
            results = _interrupted_module_results(
                manifest.modules,
                results,
                "full unittest runner interrupted between phases",
            )
            _print_results(results)
        _finalize_full_exit_code(2)
        raise SelectionError("full unittest runner interrupted") from exc
    except (OSError, SelectionError, ValueError):
        _finalize_full_exit_code(2)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("explain", "list", "run", "full"))
    parser.add_argument("--base", default=os.environ.get("CI_BASE_SHA"))
    parser.add_argument("--head", default=os.environ.get("CI_HEAD_SHA"))
    parser.add_argument("--jobs", type=_positive_int, default=DEFAULT_JOBS)
    parser.add_argument(
        "--timeout",
        type=_positive_float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=(
            "base timeout in seconds per test module before applying its "
            "TEST_TIMEOUT_CLASS multiplier (run and full actions)"
        ),
    )
    parser.add_argument(
        "--list-tests",
        action="store_true",
        help="for the full regression action, emit discovery IDs without running tests",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.list_tests and args.action != "full":
            raise SelectionError("--list-tests is valid only with the full action")
        if args.action == "full":
            return _run_full_action(args)
        core = load_core(ROOT)
        result = _selection(ROOT, core, args.base, args.head)
        if args.action == "explain":
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.action == "list":
            print("\n".join(result["selected_test_modules"]))
            return 0
        modules = result["selected_test_modules"]
        print(
            json.dumps(
                {
                    "reason": result["reason"],
                    "test_modules": modules,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if modules:
            results = _execute_modules(
                ROOT,
                modules,
                jobs=args.jobs,
                timeout_seconds=args.timeout,
            )
            _print_results(results)
            return _exit_code(results)
        return 0
    except (ImpactGraphError, OSError, SelectionError, ValueError) as exc:
        reason = exc.reason if isinstance(exc, ImpactGraphError) else "execution-error"
        print(
            "CI test selection failed: "
            + json.dumps({"reason": reason, "detail": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == INTERNAL_CHILD_BOOTSTRAP_ACTION:
        raise SystemExit(_internal_child_bootstrap_main(sys.argv[2:]))
    if len(sys.argv) == 4 and sys.argv[1] == INTERNAL_DISCOVERY_ACTION:
        raise SystemExit(_internal_discovery_main(sys.argv[2], sys.argv[3]))
    raise SystemExit(main())
