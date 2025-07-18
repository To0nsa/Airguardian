from fastapi import APIRouter
from app.schemas.schemas import HealthOut   # ← import your new schema

router = APIRouter()

@router.get(
    "/health",
    response_model=HealthOut,         # ← add response_model
    summary="Health check"
)
async def health() -> HealthOut:
    """
    Basic health check endpoint.
    Returns HTTP 200 with JSON {"success": "ok"}.
    """
    return HealthOut(success="ok")
