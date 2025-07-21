# app/api/drones.py

"""
API endpoints for fetching drone positions from an external service.
This module provides a single endpoint to list all drones with their current positions.
"""

# Standard library imports
from typing import List                   # For typing the list of DroneOut objects
from uuid import UUID                     # To parse and validate UUID strings
from fastapi import APIRouter, HTTPException  # FastAPI router and HTTP error handling
from pydantic import ValidationError      # To catch Pydantic model validation errors
import httpx                              # Async HTTP client for external API calls

# Application-specific imports
from app.core.config import settings      # To load configuration values (external API URL)
from app.core.logger import logger        # Structured logging
from app.schemas import DroneOut          # Pydantic schema for drone data

# Create a router for this module
router = APIRouter()

# External service URL, pulled from application settings
EXTERNAL_DRONES_URL = str(settings.drones_api_url)

@router.get(
    "/drones",
    response_model=List[DroneOut],                  # Declare that we return a list of DroneOut schemas
    summary="Proxy to external drone tracking API"  # OpenAPI summary
)
async def list_drones() -> List[DroneOut]:
    """
    Fetch current drone positions from the external service
    and return a list of DroneOut models, with robust error handling.
    """
    try:
        # Open an async HTTP client with a 5-second timeout
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Perform GET request to external drones API
            resp = await client.get(EXTERNAL_DRONES_URL)
            # Raise if status is 4xx/5xx
            resp.raise_for_status()

            # Attempt to parse JSON body; catch invalid JSON
            try:
                data = resp.json()
            except ValueError as exc:
                logger.error("Invalid JSON response from external API: %s", exc)
                raise HTTPException(
                    status_code=502,
                    detail="Upstream returned invalid JSON"
                )

            # At this point `data` should be a list of drone dicts
            logger.info("Fetched %d drones from external API", len(data))

            normalized: List[DroneOut] = []  # Prepare list of validated DroneOut

            # Wrap normalization loop to catch any unexpected errors
            try:
                for d in data:
                    # Extract raw fields (some may be missing)
                    raw_id = d.get("id") or d.get("drone_id")
                    owner_id = d.get("owner_id")
                    x = d.get("x")
                    y = d.get("y")
                    z = d.get("z")

                    # Skip entries missing any required field
                    if None in (raw_id, owner_id, x, y, z):
                        logger.warning(
                            "Skipping drone with missing fields: %s", d
                        )
                        continue

                    # Validate and coerce the ID into a UUID instance
                    try:
                        uuid_id = UUID(str(raw_id))
                    except (ValueError, TypeError):
                        logger.warning("Invalid drone id, skipping: %s", raw_id)
                        continue

                    # Validate and coerce all fields via Pydantic
                    try:
                        drone = DroneOut(
                            id=uuid_id,
                            owner_id=owner_id,
                            x=x,
                            y=y,
                            z=z,
                        )
                    except ValidationError as exc:
                        logger.warning(
                            "Skipping invalid drone record: %s — %s", d, exc
                        )
                        continue

                    # Append the validated model to our return list
                    normalized.append(drone)

            except Exception as exc:
                # Catch any other unexpected errors during normalization
                logger.exception("Unexpected error normalizing drones")
                raise HTTPException(
                    status_code=500,
                    detail="Internal error processing drone data"
                )

            # Return the list of DroneOut objects; FastAPI will JSON-serialize them
            return normalized

    # Handle a request timeout separately (could return 504)
    except httpx.TimeoutException as exc:
        logger.error("Timeout fetching drones", exc_info=exc)
        raise HTTPException(status_code=504, detail="Upstream timed out")

    # Handle other networking errors (DNS, connection refused, etc.)
    except httpx.RequestError as exc:
        logger.error("Network error while fetching drones", exc_info=exc)
        raise HTTPException(status_code=502, detail="Error fetching drone data")

    # Handle non-2XX HTTP status codes from upstream
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        logger.error("Upstream returned bad status %d", status)
        raise HTTPException(status_code=502, detail="Upstream error")
