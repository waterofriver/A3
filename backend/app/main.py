from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import Settings
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
    app.include_router(health_router)
    return app


app = create_app()
