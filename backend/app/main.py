from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.evaluation import router as evaluation_router
from app.api.routes.courses import media_router as course_media_router
from app.api.routes.courses import direct_media_router
from app.api.routes.courses import router as courses_router
from app.api.routes.dag import router as dag_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.learning import router as learning_router
from app.api.routes.memory import router as memory_router
from app.api.routes.profile import router as profile_router
from app.api.routes.qa import router as qa_router
from app.api.routes.quiz_practice import router as quiz_practice_router
from app.api.routes.resources import router as resources_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.users import router as users_router
from app.core.config import Settings
from app.core.errors import register_error_handlers
from app.core.logging import TraceIdMiddleware
from app.db.database import Database
from app.schemas.common import ErrorResponse
from app.services.knowledge_base_sync import sync_knowledge_base
from app.repositories.tasks import TaskRepository
from app.services.course_indexer import CourseIndexer
from app.tasks.manager import TaskManager


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()
    db = Database(resolved.database_url)
    task_manager = TaskManager()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db.create_schema()
        try:
            sync_knowledge_base(resolved.knowledge_base_root, resolved.course_root)
            CourseIndexer(db).index_root(resolved.course_root)
        except Exception as exc:
            import logging
            logging.getLogger("startup").warning(
                f"知识库同步/索引失败（不影响 API 启动）: {exc}"
            )
        with db.session() as session:
            TaskRepository(session).mark_interrupted_running_tasks()
        try:
            yield
        finally:
            provider = app.state.agent_provider
            if provider is not None and hasattr(provider, "aclose"):
                await provider.aclose()
            await task_manager.shutdown()
            db.dispose()

    error_response = {"model": ErrorResponse, "description": "统一错误响应"}
    app = FastAPI(
        title="Zhixue Engine Gateway",
        version="0.1.0",
        lifespan=lifespan,
        responses={
            400: error_response,
            404: error_response,
            503: error_response,
        },
    )
    app.state.settings = resolved
    app.state.db = db
    app.state.task_manager = task_manager
    app.state.agent_provider = None
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.allowed_web_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Task-ID", "X-Trace-ID"],
    )
    app.add_middleware(TraceIdMiddleware)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(dag_router)
    app.include_router(dashboard_router)
    app.include_router(evaluation_router)
    app.include_router(courses_router)
    app.include_router(course_media_router)
    app.include_router(direct_media_router)
    app.include_router(learning_router)
    app.include_router(memory_router)
    app.include_router(users_router)
    app.include_router(profile_router)
    app.include_router(qa_router)
    app.include_router(quiz_practice_router)
    app.include_router(resources_router)
    app.include_router(tasks_router)
    return app


app = create_app()
