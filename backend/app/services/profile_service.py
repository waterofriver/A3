from collections.abc import AsyncIterator

from app.agents.base import AgentProvider
from app.db.database import Database
from app.db.models import ProfileMessage
from app.repositories.profiles import ProfileRepository
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository
from app.schemas.profile import StudentProfileData
from app.schemas.task import GatewayEvent


def encode_sse(event: GatewayEvent) -> str:
    return (
        f"id: {event.seq}\n"
        f"event: {event.event}\n"
        f"data: {event.model_dump_json()}\n\n"
    )


class ProfileService:
    def __init__(self, db: Database, provider: AgentProvider):
        self.db = db
        self.provider = provider

    def create_task(self, user_id: str, chat_text: str) -> str:
        with self.db.session() as session:
            user = UserRepository(session).get_or_create(user_id)
            task = TaskRepository(session).create(
                user_id=user.id,
                task_type="profile",
                request_snapshot={"chat_text": chat_text},
            )
            session.add(
                ProfileMessage(
                    user_id=user.id,
                    task_id=task.id,
                    role="user",
                    content=chat_text,
                )
            )
            session.flush()
            return task.id

    async def stream_profile(
        self,
        *,
        task_id: str,
        trace_id: str,
        user_id: str,
        chat_text: str,
    ) -> AsyncIterator[str]:
        with self.db.session() as session:
            current_record = ProfileRepository(session).get(user_id)
            current_profile = (
                StudentProfileData.model_validate(current_record.profile_data)
                if current_record
                else None
            )
            current_revision = current_record.revision if current_record else 0

        latest_profile = current_profile
        assistant_parts: list[str] = []

        async for event in self.provider.stream_profile(
            task_id=task_id,
            trace_id=trace_id,
            user_id=user_id,
            chat_text=chat_text,
            current_profile=current_profile,
        ):
            if event.event == "content.delta":
                assistant_parts.append(event.content)

            with self.db.session() as session:
                task_repository = TaskRepository(session)
                stored_event = task_repository.append_event(
                    task_id, event.event, event.model_dump(mode="json")
                )
                event.seq = stored_event.seq

                if event.event == "profile.patch" and event.profile_patch:
                    merged = {
                        **(latest_profile.model_dump() if latest_profile else {}),
                        **event.profile_patch,
                    }
                    latest_profile = StudentProfileData.model_validate(merged)
                    current_revision += 1
                    ProfileRepository(session).upsert(
                        user_id,
                        latest_profile.model_dump(),
                        revision=current_revision,
                    )

                status = "running"
                result_snapshot = None
                if event.event == "task.completed":
                    status = "succeeded"
                    result_snapshot = {
                        "profile": latest_profile.model_dump()
                        if latest_profile
                        else None,
                        "revision": current_revision,
                    }
                    if assistant_parts:
                        session.add(
                            ProfileMessage(
                                user_id=user_id,
                                task_id=task_id,
                                role="assistant",
                                content="".join(assistant_parts),
                            )
                        )
                elif event.event == "task.failed":
                    status = "failed"

                task_repository.update_state(
                    task_id,
                    status=status,
                    progress=event.progress,
                    current_agent=event.current_agent,
                    result_snapshot=result_snapshot,
                    error=event.error.model_dump() if event.error else None,
                )
                stored_event.payload = event.model_dump(mode="json")
                session.flush()

            yield encode_sse(event)
