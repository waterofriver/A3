import asyncio
import json
from collections.abc import AsyncIterator
from time import monotonic

from app.db.database import Database

TERMINAL_EVENTS = {"task.completed", "task.failed"}
TERMINAL_STATUSES = {"succeeded", "failed", "partial_success"}


def encode_stored_event(seq: int, event_type: str, payload: dict) -> str:
    data = {**payload, "event": event_type, "seq": seq}
    return (
        f"id: {seq}\n"
        f"event: {event_type}\n"
        f"data: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"
    )


async def stream_persisted_task_events(
    *,
    db: Database,
    task_id: str,
    after_seq: int,
    poll_interval_ms: int,
    heartbeat_seconds: int,
) -> AsyncIterator[str]:
    cursor = after_seq
    last_output = monotonic()

    while True:
        with db.session() as session:
            from app.repositories.tasks import TaskRepository

            repository = TaskRepository(session)
            task = repository.get(task_id)
            events = repository.list_events(task_id, cursor)
            task_status = task.status

        for event in events:
            cursor = event.seq
            last_output = monotonic()
            yield encode_stored_event(event.seq, event.event_type, event.payload)
            if event.event_type in TERMINAL_EVENTS:
                return

        if not events and task_status in TERMINAL_STATUSES:
            return

        if heartbeat_seconds > 0 and monotonic() - last_output >= heartbeat_seconds:
            heartbeat = {
                "event": "heartbeat",
                "task_id": task_id,
                "seq": cursor,
                "progress": 0,
                "finish_flag": False,
            }
            yield (
                "event: heartbeat\n"
                f"data: {json.dumps(heartbeat, separators=(',', ':'))}\n\n"
            )
            last_output = monotonic()

        await asyncio.sleep(max(1, poll_interval_ms) / 1000)
