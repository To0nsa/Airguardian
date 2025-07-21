# app/api/nfz.py

"""
API endpoints for managing No-Fly Zone (NFZ) violations.
This module provides an endpoint to list NFZ violations from the last 24 hours.
"""

from typing import List, Sequence
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timedelta, timezone

from app.core.config import settings      # Application configuration (X-Secret value)
from app.db.session import get_db        # Dependency to retrieve DB session
from app.db.models import Violation as ViolationModel  # ORM model for violations
from app.core.logger import logger       # Centralized logger
from app.schemas.schemas import ViolationOut  # Pydantic schema for response model

# Create a router for NFZ (No-Fly Zone) related endpoints
router = APIRouter()

@router.get(
    "/nfz",
    response_model=List[ViolationOut],  # Returns a list of ViolationOut models
    summary="List NFZ violations from the last 24h"
)
# Declare return type as Sequence to satisfy static typing covariance
def get_violations(
    x_secret: str = Header(..., alias="X-Secret"),  # Extract X-Secret header for auth
    db: Session = Depends(get_db),                  # Inject DB session
) -> Sequence[ViolationOut]:
    """
    Fetches all NFZ violations in the past 24 hours.

    - Validates X-Secret header for authentication.
    - Queries the database with eager-loading of related drone and owner.
    - Handles DB errors gracefully and logs the result.
    """
    try:
        # 1. Authentication
        if x_secret != settings.x_secret:
            logger.warning("Unauthorized NFZ access attempt")
            raise HTTPException(
                status_code=401,
                detail="Invalid X-Secret",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # 2. Compute UTC cutoff timestamp (24 hours ago)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        logger.debug("Fetching violations since %s", cutoff.isoformat())

        # 3. Database query with eager-loading
        try:
            violations = (
                db.query(ViolationModel)
                .options(
                    joinedload(ViolationModel.drone),  # Load related Drone object
                    joinedload(ViolationModel.owner)   # Load related Owner object
                )
                .filter(ViolationModel.timestamp >= cutoff)  # Only recent records
                .all()
            )
        except OperationalError as e:
            logger.error("Database timeout fetching violations: %s", e)
            raise HTTPException(status_code=504, detail="Database timed out")
        except SQLAlchemyError as e:
            logger.error("Database error fetching violations: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )

        # 4. Logging and return
        # FastAPI will use Pydantic's .from_attributes via response_model to serialize
        logger.info("Returned %d violations", len(violations))
        return violations

    except HTTPException:
        # Propagate HTTPExceptions as-is
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.exception("Unexpected error in get_violations")
        raise HTTPException(status_code=500, detail="Internal server error")