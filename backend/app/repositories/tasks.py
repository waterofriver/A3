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

    def find_idempotent(self, user_id: str, idempotency_key: str) -> Task | None:
        return self.session.scalar(
            select(Task).where(
                Task.user_id == user_id,
                Task.idempotency_key == idempotency_key,
            )
        )

    def get_request_snapshot(self, task_id: str) -> dict:
        return dict(self.get(task_id).request_snapshot)

    def list_events(self, task_id: str, after_seq: int = 0) -> list[TaskEvent]:
        statement = (
            select(TaskEvent)
            .where(TaskEvent.task_id == task_id, TaskEvent.seq > after_seq)
            .order_by(TaskEvent.seq)
        )
        return list(self.session.scalars(statement))

    def mark_interrupted_running_tasks(self) -> int:
        tasks = list(
            self.session.scalars(
                select(Task).where(Task.status.in_(["queued", "running"]))
            )
        )
        for task in tasks:
            task.status = "failed"
            task.error = {
                "code": "TASK_INTERRUPTED",
                "message": "服务重启中断了任务，请重新提交。",
                "retryable": True,
            }
            stored = self.append_event(
                task.id,
                "task.failed",
                {
                    "event": "task.failed",
                    "task_id": task.id,
                    "seq": 0,
                    "trace_id": "startup-recovery",
                    "current_agent": task.current_agent,
                    "progress": task.progress,
                    "resource_type": None,
                    "content": "",
                    "media_url": None,
                    "finish_flag": True,
                    "resource_ids": [],
                    "profile_patch": None,
                    "error": task.error,
                    "demo_mode": False,
                },
            )
            stored.payload["seq"] = stored.seq
        self.session.flush()
        return len(tasks)

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
