from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    request.app.state.db.ping()
    return {
        "status": "ok",
        "database": "ok",
        "agent_mode": request.app.state.settings.agent_mode,
    }
