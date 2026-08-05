from __future__ import annotations

from collections import deque
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any


TaskFunction = Callable[[], Any]
TaskCompletion = Callable[[bool, object, str], None]


@dataclass(slots=True)
class DeviceTask:
    fn: TaskFunction
    on_complete: TaskCompletion
    kind: str = "action"
    coalesce_key: str | None = None


class DeviceTaskCoordinator:
    """Serialize SDK access while preserving user-task FIFO order."""

    def __init__(self, *, thread_name_prefix: str = "dlcpro") -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=thread_name_prefix)
        self._queue: deque[DeviceTask] = deque()
        self._active_task: DeviceTask | None = None
        self._active_future: Future | None = None
        self._polling_enabled = True
        self._shutdown = False

    @property
    def has_work(self) -> bool:
        return self._active_future is not None or bool(self._queue)

    @property
    def has_user_work(self) -> bool:
        if self._active_task is not None and self._active_task.kind != "poll":
            return True
        return any(task.kind != "poll" for task in self._queue)

    @property
    def active_kind(self) -> str | None:
        return self._active_task.kind if self._active_task is not None else None

    def submit(
        self,
        fn: TaskFunction,
        on_complete: TaskCompletion,
        *,
        kind: str = "action",
        coalesce_key: str | None = None,
    ) -> bool:
        if self._shutdown or (kind == "poll" and not self._polling_enabled):
            return False
        if kind == "poll" and self._has_kind("poll"):
            return False

        task = DeviceTask(fn=fn, on_complete=on_complete, kind=kind, coalesce_key=coalesce_key)
        if coalesce_key is not None and self._replace_queued_task(task):
            return True
        self._queue.append(task)
        self._start_next()
        return True

    def poll_completed(self) -> bool:
        future = self._active_future
        task = self._active_task
        if future is None or task is None or not future.done():
            return False

        self._active_future = None
        self._active_task = None
        try:
            result = future.result()
        except Exception as exc:  # noqa: BLE001
            task.on_complete(False, exc, task.kind)
        else:
            task.on_complete(True, result, task.kind)
        self._start_next()
        return True

    def stop_polling_and_clear(self) -> None:
        self._polling_enabled = False
        self._queue.clear()

    def resume_polling(self) -> None:
        self._polling_enabled = True

    def clear_pending(self) -> None:
        self._queue.clear()

    def shutdown(self) -> None:
        self._shutdown = True
        self._queue.clear()
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _has_kind(self, kind: str) -> bool:
        if self._active_task is not None and self._active_task.kind == kind:
            return True
        return any(task.kind == kind for task in self._queue)

    def _replace_queued_task(self, replacement: DeviceTask) -> bool:
        for index, queued in enumerate(self._queue):
            if queued.coalesce_key == replacement.coalesce_key:
                self._queue[index] = replacement
                return True
        return False

    def _start_next(self) -> None:
        if self._shutdown or self._active_future is not None or not self._queue:
            return
        self._active_task = self._queue.popleft()
        self._active_future = self._executor.submit(self._active_task.fn)
