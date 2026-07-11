from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def uuid_string() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True
    )
    profile_data: Mapped[dict] = mapped_column(JSON, default=dict)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "idempotency_key", name="uq_tasks_user_idempotency_key"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    task_type: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(24), default="queued", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_agent: Mapped[str | None] = mapped_column(String(80), nullable=True)
    request_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    result_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class ProfileMessage(Base):
    __tablename__ = "profile_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    task_id: Mapped[str | None] = mapped_column(
        ForeignKey("tasks.id"), nullable=True, index=True
    )
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TaskEvent(Base):
    __tablename__ = "task_events"
    __table_args__ = (
        UniqueConstraint("task_id", "seq", name="uq_task_events_task_seq"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    course_name: Mapped[str] = mapped_column(String(160), index=True)
    resource_type: Mapped[str] = mapped_column(String(24), index=True)
    title: Mapped[str] = mapped_column(String(240))
    payload: Mapped[dict] = mapped_column(JSON)
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LearningPath(Base):
    __tablename__ = "learning_paths"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "course_name", "version", name="uq_learning_path_version"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    course_name: Mapped[str] = mapped_column(String(160), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(24), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LearningPathNode(Base):
    __tablename__ = "learning_path_nodes"
    __table_args__ = (
        UniqueConstraint("path_id", "position", name="uq_learning_path_node_position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    path_id: Mapped[str] = mapped_column(ForeignKey("learning_paths.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    stage_name: Mapped[str] = mapped_column(String(120))
    difficulty: Mapped[str] = mapped_column(String(24))
    resource_id: Mapped[str | None] = mapped_column(
        ForeignKey("resources.id"), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    resource_id: Mapped[str] = mapped_column(ForeignKey("resources.id"), index=True)
    answers: Mapped[dict] = mapped_column(JSON)
    results: Mapped[list] = mapped_column(JSON)
    score: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    course_name: Mapped[str] = mapped_column(String(160), index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    resource_id: Mapped[str | None] = mapped_column(
        ForeignKey("resources.id"), nullable=True, index=True
    )
    path_node_id: Mapped[str | None] = mapped_column(
        ForeignKey("learning_path_nodes.id"), nullable=True, index=True
    )
    client_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    client_ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "course_name",
            "evidence_hash",
            name="uq_evaluation_report_evidence",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    course_name: Mapped[str] = mapped_column(String(160), index=True)
    theory_score: Mapped[int] = mapped_column(Integer)
    practice_score: Mapped[int] = mapped_column(Integer)
    weak_points: Mapped[list] = mapped_column(JSON, default=list)
    recommended_changes: Mapped[list] = mapped_column(JSON, default=list)
    source_path_id: Mapped[str] = mapped_column(
        ForeignKey("learning_paths.id"), index=True
    )
    applied_path_id: Mapped[str | None] = mapped_column(
        ForeignKey("learning_paths.id"), nullable=True, index=True
    )
    evidence_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Course(Base):
    __tablename__ = "courses"

    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    root_path: Mapped[str] = mapped_column(String(1000))
    content_ready: Mapped[bool] = mapped_column(default=False)
    is_demo: Mapped[bool] = mapped_column(default=False)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CourseDocument(Base):
    __tablename__ = "course_documents"
    __table_args__ = (
        UniqueConstraint(
            "course_slug",
            "relative_path",
            name="uq_course_document_relative_path",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    course_slug: Mapped[str] = mapped_column(
        ForeignKey("courses.slug"), index=True
    )
    chapter_path: Mapped[str] = mapped_column(String(500))
    chapter_name: Mapped[str] = mapped_column(String(160))
    relative_path: Mapped[str] = mapped_column(String(1000))
    filename: Mapped[str] = mapped_column(String(260))
    file_type: Mapped[str] = mapped_column(String(24))
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer)
    preview_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(1200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
