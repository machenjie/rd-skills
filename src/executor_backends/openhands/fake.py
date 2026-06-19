"""Offline fake OpenHands backend for adapter tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .protocol import BackendEvent, BackendTaskHandle


@dataclass
class FakeOpenHandsBackend:
    """Deterministic backend that never executes commands or touches files."""

    events: tuple[BackendEvent, ...] = ()
    changed_paths: tuple[str, ...] = ()
    validation_results: tuple[Mapping[str, object], ...] = ()
    _started: bool = field(default=False, init=False)
    _stopped: bool = field(default=False, init=False)

    def start_task(self, task: Mapping[str, object]) -> BackendTaskHandle:
        self._started = True
        return BackendTaskHandle(
            task_id=str(task.get("task_id") or "fake-openhands-task"),
            sandbox_id=str(task.get("sandbox_id") or "fake-sandbox"),
        )

    def observe_events(self, handle: BackendTaskHandle) -> Iterable[BackendEvent]:
        if not self._started:
            return ()
        return self.events

    def collect_changed_paths(self, handle: BackendTaskHandle) -> tuple[str, ...]:
        return self.changed_paths

    def collect_validation_results(self, handle: BackendTaskHandle) -> tuple[Mapping[str, object], ...]:
        return self.validation_results

    def stop_task(self, handle: BackendTaskHandle) -> None:
        self._stopped = True

    @property
    def stopped(self) -> bool:
        return self._stopped


__all__ = ["FakeOpenHandsBackend"]
