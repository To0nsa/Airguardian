import os
from fastapi import FastAPI
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger

from app.api.health import router as health_router
from app.api.drones import router as drones_router
from app.api.nfz import router as nfz_router


def create_app() -> FastAPI:
    """
    Factory to create FastAPI app and include all routers.
    """
    app = FastAPI(
        title="Airguardian",
        description="Real-time NFZ violation detection for drones",
        version="0.1.0",
        debug=settings.debug
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # All road under /api/v1
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(drones_router,   prefix="/api/v1")
    app.include_router(nfz_router,      prefix="/api/v1")
    return app


app = create_app()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@health_router.get("/health", summary="Health check")
async def health():
    logger.info("Health endpoint called")
    return {"success": "ok"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
