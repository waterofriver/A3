import asyncio
from collections.abc import Coroutine
from typing import Any


class TaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[Any]] = {}

    def start(self, task_id: str, coroutine: Coroutine[Any, Any, Any]) -> bool:
        current = self._tasks.get(task_id)
        if current is not None and not current.done():
            coroutine.close()
            return False

        task = asyncio.create_task(coroutine, name=f"gateway-task:{task_id}")
        self._tasks[task_id] = task
        task.add_done_callback(
            lambda finished, current_id=task_id: self._finish(current_id, finished)
        )
        return True

    def is_running(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        return task is not None and not task.done()

    def _finish(self, task_id: str, task: asyncio.Task[Any]) -> None:
        if self._tasks.get(task_id) is task:
            self._tasks.pop(task_id, None)
        if not task.cancelled():
            task.exception()

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
