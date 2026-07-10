import asyncio

import pytest

from app.tasks.manager import TaskManager


@pytest.mark.asyncio
async def test_task_manager_deduplicates_and_cleans_completed_runners():
    manager = TaskManager()
    release = asyncio.Event()

    async def runner():
        await release.wait()

    assert manager.start("task-1", runner()) is True
    duplicate = runner()
    assert manager.start("task-1", duplicate) is False
    duplicate.close()
    assert manager.is_running("task-1") is True

    release.set()
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert manager.is_running("task-1") is False


@pytest.mark.asyncio
async def test_task_manager_cancels_runners_on_shutdown():
    manager = TaskManager()

    async def runner():
        await asyncio.Event().wait()

    assert manager.start("task-2", runner()) is True
    await manager.shutdown()

    assert manager.is_running("task-2") is False
