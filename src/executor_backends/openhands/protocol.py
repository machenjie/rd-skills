"""Minimal OpenHands executor backend protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Protocol


@dataclass(frozen=True)
class BackendTaskHandle:
    """Bounded handle returned by an execution backend."""

    task_id: str
    sandbox_id: str | None = None


@dataclass(frozen=True)
class BackendEvent:
    """Bounded backend event that can be passed to the OpenHands adapter."""

    event_type: str
    data: Mapping[str, object] = field(default_factory=dict)

    def to_adapter_payload(self) -> dict[str, object]:
        payload = dict(self.data)
        payload.setdefault("event_type", self.event_type)
        return payload


class OpenHandsBackend(Protocol):
    """Protocol for execution backends without prescribing transport details."""

    def start_task(self, task: Mapping[str, object]) -> BackendTaskHandle:
        ...

    def observe_events(self, handle: BackendTaskHandle) -> Iterable[BackendEvent]:
        ...

    def collect_changed_paths(self, handle: BackendTaskHandle) -> tuple[str, ...]:
        ...

    def collect_validation_results(self, handle: BackendTaskHandle) -> tuple[Mapping[str, object], ...]:
        ...

    def stop_task(self, handle: BackendTaskHandle) -> None:
        ...


__all__ = ["BackendEvent", "BackendTaskHandle", "OpenHandsBackend"]
