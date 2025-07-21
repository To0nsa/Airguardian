# app/api/health.py

"""
API endpoint for basic health check.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from app.schemas.schemas import HealthOut
from app.db.session import get_db
from app.core.logger import logger

# Initialize router for health-related endpoints
router = APIRouter()

@router.get(
    "/health",
    response_model=HealthOut,  # Defines the output schema for the endpoint
    summary="Health check"  # Short description shown in OpenAPI docs
)
async def health(
    db: Session = Depends(get_db)  # Injects a SQLAlchemy DB session via dependency
) -> HealthOut:
    """
    Basic health check endpoint.
    - Executes a simple SELECT 1 query to verify database connectivity.
    - Returns HTTP 200 with JSON {"status": "ok"} on success.
    - Returns HTTP 503 with detail "Database unavailable" if the database cannot be reached.
    """
    try:
        # Perform a minimal query; wrap raw SQL with text() for SQLAlchemy 2.x compatibility
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as e:
        # Log the database connectivity error and return a 503 Service Unavailable
        logger.error("Health check failed: cannot reach database: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )

    # If execution reaches here, DB is reachable
    return HealthOut(status="ok")
