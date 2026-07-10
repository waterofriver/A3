from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agents.mock import MockAgentProvider
from app.api.routes.health import router as health_router
from app.api.routes.profile import router as profile_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.users import router as users_router
from app.core.config import Settings
from app.core.errors import register_error_handlers
from app.core.logging import TraceIdMiddleware
from app.db.database import Database


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()
    db = Database(resolved.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db.create_schema()
        yield
        db.dispose()

    app = FastAPI(title="Zhixue Engine Gateway", version="0.1.0", lifespan=lifespan)
    app.state.settings = resolved
    app.state.db = db
    app.state.agent_provider = (
        MockAgentProvider(resolved) if resolved.agent_mode == "mock" else None
    )
    app.add_middleware(TraceIdMiddleware)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(users_router)
    app.include_router(profile_router)
    app.include_router(tasks_router)
    return app


app = create_app()
