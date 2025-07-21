# app/main.py

import sys
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.core.config import settings
from app.core.logger import logger

from app.api.health import router as health_router
from app.api.drones import router as drones_router
from app.api.nfz import router as nfz_router

from app.db.session import engine


def create_app() -> FastAPI:
    """
    Factory to create FastAPI app, include routers, and configure global error handling.
    """
    app = FastAPI(
        title="Airguardian",
        description="Real-time NFZ violation detection for drones",
        version="0.1.0",
        debug=settings.debug
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers under /api/v1
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(drones_router, prefix="/api/v1")
    app.include_router(nfz_router, prefix="/api/v1")

    # Exception handler for request validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error("Validation error: %s - Body: %s", exc.errors(), exc.body)
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "body": exc.body},
        )

    # Exception handler for HTTP exceptions
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning("HTTP exception: status_code=%s, detail=%s", exc.status_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    # Catch-all handler for unhandled exceptions
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception occurred: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Startup event: verify database connectivity
    @app.on_event("startup")
    async def startup_event():
        try:
            conn = engine.connect()
            conn.execute(text("SELECT 1"))
            conn.close()
            logger.info("Database connection successful at startup.")
        except Exception as e:
           logger.error("Database connection failed at startup: %s", e)
           sys.exit("Startup aborted due to database connection failure.")

    # Shutdown event: log shutdown completion
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutdown complete.")

    # Root redirect to docs
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.debug
    )
