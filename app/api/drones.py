from typing import List
from fastapi import APIRouter, HTTPException
import httpx
from app.core.logger import logger
from app.schemas.schemas import DroneOut

router = APIRouter()

EXTERNAL_DRONES_URL = "https://drones-api.hive.fi/drones"

@router.get(
    "/drones",
    response_model=List[DroneOut],
    summary="Proxy to external drone tracking API"
)
async def list_drones() -> List[DroneOut]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(EXTERNAL_DRONES_URL)
            resp.raise_for_status()
            data = resp.json()
            logger.info("Fetched %d drones from external API", len(data))

            normalized = []
            for d in data:
                # Try to get a unique drone ID, otherwise synthesize one
                drone_id = d.get("id") or d.get("drone_id")
                owner_id = d.get("owner_id")
                x = d.get("x")
                y = d.get("y")
                z = d.get("z")
                if owner_id is None or x is None or y is None or z is None:
                    logger.warning("Skipping drone with missing fields: %s", d)
                    continue
                if not drone_id:
                    # Synthesize a unique ID based on owner and position
                    drone_id = f"{owner_id}_{x}_{y}_{z}"
                normalized.append({
                    "id": drone_id,
                    "x": x,
                    "y": y,
                    "z": z,
                    "owner_id": owner_id,
                })
            return normalized
    except httpx.RequestError as e:
        logger.error("Network error while fetching drones", exc_info=e)
        raise HTTPException(status_code=502, detail="Error fetching drone data")
    except httpx.HTTPStatusError as e:
        logger.error("Upstream returned bad status %s", e.response.status_code)
        raise HTTPException(status_code=502, detail="Upstream error")
