from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Task, TaskEvent


class TaskRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        user_id: str,
        task_type: str,
        request_snapshot: dict,
        idempotency_key: str | None = None,
    ) -> Task:
        task = Task(
            id=str(uuid4()),
            user_id=user_id,
            task_type=task_type,
            request_snapshot=request_snapshot,
            idempotency_key=idempotency_key,
        )
        self.session.add(task)
        self.session.flush()
        return task

    def get(self, task_id: str) -> Task:
        task = self.session.get(Task, task_id)
        if task is None:
            raise LookupError(task_id)
        return task

    def append_event(self, task_id: str, event_type: str, payload: dict) -> TaskEvent:
        next_seq = self.session.scalar(
            select(func.coalesce(func.max(TaskEvent.seq), 0) + 1).where(
                TaskEvent.task_id == task_id
            )
        )
        event = TaskEvent(
            id=str(uuid4()),
            task_id=task_id,
            seq=int(next_seq),
            event_type=event_type,
            payload=payload,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def update_state(
        self,
        task_id: str,
        *,
        status: str,
        progress: int,
        current_agent: str | None = None,
        result_snapshot: dict | None = None,
        error: dict | None = None,
    ) -> Task:
        task = self.get(task_id)
        task.status = status
        task.progress = progress
        task.current_agent = current_agent
        if result_snapshot is not None:
            task.result_snapshot = result_snapshot
        task.error = error
        self.session.flush()
        return task
