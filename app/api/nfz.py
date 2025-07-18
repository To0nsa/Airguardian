from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.config import settings
from app.db.session import get_db
from app.db.models import Violation as ViolationModel
from app.core.logger import logger
from app.schemas.schemas import ViolationOut  # ← import your new schema

router = APIRouter()

@router.get(
    "/nfz",
    response_model=List[ViolationOut],        # ← use the ViolationOut schema
    summary="List NFZ violations from the last 24h"
)
async def get_violations(
    x_secret: str = Header(..., alias="X-Secret"),
    db: Session = Depends(get_db),
) -> List[ViolationOut]:
    if x_secret != settings.x_secret:
        logger.warning("Unauthorized NFZ access attempt")
        raise HTTPException(status_code=401, detail="Invalid X-Secret")

    cutoff = datetime.utcnow() - timedelta(hours=24)
    rows = db.query(ViolationModel).filter(ViolationModel.timestamp >= cutoff).all()

    result: List[ViolationOut] = []
    for v in rows:
        result.append(
            ViolationOut(
                drone_id=v.drone_id,
                timestamp=v.timestamp.isoformat(),
                position={"x": v.x, "y": v.y, "z": v.z},
                owner={
                    "first": v.owner_first,
                    "last": v.owner_last,
                    "ssn": v.owner_ssn,
                    "phone": v.owner_phone,
                }
            )
        )

    logger.info("Returned %d violations", len(result))
    return result
