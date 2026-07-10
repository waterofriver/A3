from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.mock import MockAgentProvider
from app.api.routes.health import router as health_router
from app.api.routes.profile import router as profile_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.users import router as users_router
from app.core.config import Settings
from app.core.errors import register_error_handlers
from app.core.logging import TraceIdMiddleware
from app.db.database import Database
from app.schemas.common import ErrorResponse


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()
    db = Database(resolved.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db.create_schema()
        yield
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
    app.state.agent_provider = (
        MockAgentProvider(resolved) if resolved.agent_mode == "mock" else None
    )
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
    app.include_router(users_router)
    app.include_router(profile_router)
    app.include_router(tasks_router)
    return app


app = create_app()
