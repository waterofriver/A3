from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import StudentProfile, utcnow


class ProfileRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, user_id: str) -> StudentProfile | None:
        return self.session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )

    def upsert(self, user_id: str, profile: dict, revision: int) -> StudentProfile:
        current = self.get(user_id)
        if current is None:
            current = StudentProfile(
                id=str(uuid4()),
                user_id=user_id,
                profile_data=profile,
                revision=revision,
            )
            self.session.add(current)
        else:
            current.profile_data = profile
            current.revision = revision
        self.session.flush()
        return current

    def confirm(self, user_id: str) -> StudentProfile:
        profile = self.get(user_id)
        if profile is None:
            raise LookupError(user_id)
        profile.confirmed_at = utcnow()
        self.session.flush()
        return profile
