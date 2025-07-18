# app/tasks/fetch_and_detect.py

import uuid
from datetime import datetime
import httpx
from app.celery import celery_app
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import Violation, NFZActive
from app.core.logger import logger

@celery_app.task(name='app.tasks.fetch_and_process_drones')
def fetch_and_process_drones():
    from sqlalchemy.exc import IntegrityError

    try:
        response = httpx.get(str(settings.drones_api_url), timeout=5.0)
        response.raise_for_status()
        drones = response.json()
        logger.info("Fetched %d drones", len(drones))
    except httpx.RequestError as exc:
        logger.error("Network error fetching drones: %s", exc)
        return
    except httpx.HTTPStatusError as exc:
        logger.error("Error response %s from drones API", exc.response.status_code)
        return

    db = SessionLocal()
    try:
        active_drone_ids = {row.drone_id for row in db.query(NFZActive.drone_id).all()}
        new_inside_nfz = set()

        for drone in drones:
            drone_id = drone.get("id") or drone.get("drone_id")
            if not drone_id:
                drone_id = str(uuid.uuid4())
            owner_id = drone.get('owner_id')
            x = drone.get('x')
            y = drone.get('y')
            z = drone.get('z')
            if drone_id is None or owner_id is None or x is None or y is None:
                logger.warning("Skipping drone with missing fields: %s", drone)
                continue

            inside = (x * x + y * y) <= 1000**2

            if inside:
                new_inside_nfz.add(drone_id)
                if drone_id not in active_drone_ids:
                    try:
                        user_resp = httpx.get(f"{str(settings.users_api_url)}/{owner_id}", timeout=5.0)
                        user_resp.raise_for_status()
                        owner = user_resp.json()
                    except Exception as exc:
                        logger.error("Failed to fetch owner %s: %s", owner_id, exc)
                        continue

                    violation = Violation(
                        id=str(uuid.uuid4()),
                        drone_id=drone_id,
                        timestamp=datetime.utcnow(),
                        x=x,
                        y=y,
                        z=z,
                        owner_first=owner.get('first_name') or "",
                        owner_last=owner.get('last_name') or "",
                        owner_ssn=owner.get('social_security_number') or "",
                        owner_phone=owner.get('phone_number') or "",
                    )
                    db.add(violation)
                    db.add(NFZActive(drone_id=drone_id))
                    logger.info("Violation: drone %s entered NFZ", drone_id)
            else:
                if drone_id in active_drone_ids:
                    db.query(NFZActive).filter_by(drone_id=drone_id).delete()
                    logger.info("Drone %s left NFZ, tracking stopped", drone_id)

        db.commit()
        return {"processed": len(drones), "new_violations": len(new_inside_nfz)}
    except Exception:
        db.rollback()
        logger.exception("Error processing drone violations")
    finally:
        db.close()

celery_app.conf.beat_schedule = {
    'fetch-and-process-drones-every-10-seconds': {
        'task': 'app.tasks.fetch_and_process_drones',
        'schedule': 10.0,
    },
}
