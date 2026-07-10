from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, user_id: str) -> User | None:
        return self.session.get(User, user_id)

    def get_or_create(self, user_id: str) -> User:
        user = self.get(user_id)
        if user is None:
            user = User(id=user_id)
            self.session.add(user)
            self.session.flush()
        return user
