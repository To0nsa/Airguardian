'''  
Periodic Celery task to fetch drone positions, detect NFZ violations,
fetch owner details, and record violations in the database.
'''

from uuid import UUID  # For drone IDs
from datetime import datetime, timezone  # For timezone-aware timestamps
import httpx  # HTTP client for external API calls
from sqlalchemy.exc import IntegrityError, SQLAlchemyError  # DB error handling

from app.celery import celery_app  # Celery application instance
from app.core.config import settings  # Application configuration (URLs, secrets, etc.)
from app.db.session import SessionLocal  # Database session factory
from app.db.models import Violation, NFZActive, Drone, Owner  # ORM models for violations, active NFZ entries, drones, and owners
from app.core.logger import logger  # Centralized logger

def fetch_drones(timeout: float = 5.0) -> list[dict]:
    """
    Fetch raw drone list from the external API.
    """
    resp = httpx.get(str(settings.drones_api_url), timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def parse_drone(raw: dict) -> tuple[UUID, int, int, int, int]:
    """
    Extract and validate required fields from raw drone data.
    """
    drone_id = UUID(str(raw.get("id")))
    owner_id = raw["owner_id"]
    x, y, z = raw["x"], raw["y"], raw.get("z", 0)
    return drone_id, owner_id, int(x), int(y), int(z)


def fetch_owner(owner_id: int, timeout: int = 5.0) -> dict:
    """
    Fetch owner information for a given owner_id from the external API.
    """
    resp = httpx.get(f"{settings.users_api_url}/{owner_id}", timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def record_violation(
    db,
    drone_id: str,
    x: int,
    y: int,
    z: int,
    owner: dict
) -> None:
    """
    Create a Violation record and corresponding NFZActive entry in the database.
    """
    owner_id = owner.get("id")
    # Ensure owner exists
    db_owner = db.query(Owner).filter_by(id=owner_id).first()
    if not db_owner:
        db_owner = Owner(
            id=owner_id,
            first_name=owner.get("first_name", ""),
            last_name=owner.get("last_name", ""),
            email=owner.get("email", ""),
            phone_number=owner.get("phone_number", ""),
            social_security_number=owner.get("social_security_number", ""),
            purchased_at=owner.get("purchased_at", ""),
        )
        db.add(db_owner)
        db.flush()

    # Ensure drone exists
    drone = db.query(Drone).filter_by(id=drone_id).first()
    if not drone:
        drone = Drone(
            id=drone_id,
            owner_id=owner_id,
            x=x, y=y, z=z
        )
        db.add(drone)
        db.flush()

    violation = Violation(
        drone_id=drone_id,
        owner_id=owner_id,
        timestamp=datetime.now(timezone.utc),
        x=x, y=y, z=z,
    )
    db.add(violation)

    # Only create NFZActive if not already present
    nfz = db.query(NFZActive).filter_by(drone_id=drone_id).first()
    if not nfz:
        db.add(NFZActive(drone_id=drone_id, owner_id=owner_id))


def process_drones(drones: list[dict], db) -> tuple[int, int]:
    """
    Process a batch of drones:
    - Parse each drone entry
    - Check if it's within the NFZ (radius = 1000)
    - Record new violations and mark active breaches
    - Remove NFZActive entries when drones leave
    """
    active_ids = {row.drone_id for row in db.query(NFZActive.drone_id)}
    seen_inside = set()
    new_violations = set()

    for raw in drones:
        try:
            drone_id, owner_id, x, y, z = parse_drone(raw)
        except (KeyError, TypeError, ValueError):
            logger.warning("Skipping malformed drone: %s", raw)
            continue

        inside = (x * x + y * y) <= 1000**2

        if inside:
            seen_inside.add(drone_id)
            if drone_id not in active_ids:
                try:
                    owner = fetch_owner(owner_id)
                    record_violation(db, drone_id, x, y, z, owner)
                    new_violations.add(drone_id)
                    logger.info("Violation recorded for drone %s", drone_id)
                except httpx.HTTPError as e:
                    logger.error("Owner fetch failed (%s): %s", owner_id, e)
                except IntegrityError as e:
                    logger.warning("DB integrity error for %s: %s", drone_id, e)
                    db.rollback()
                except SQLAlchemyError as e:
                    logger.error("DB error recording violation: %s", e)
                    db.rollback()
        else:
            if drone_id in active_ids:
                try:
                    # Update any open violation exit timestamp if using that pattern
                    db.query(NFZActive).filter_by(drone_id=drone_id).delete()
                    logger.info("Drone %s left NFZ", drone_id)
                except SQLAlchemyError as e:
                    logger.warning(
                        "Failed to remove NFZActive for %s: %s", drone_id, e
                    )
                    db.rollback()

    return len(drones), len(new_violations)


@celery_app.task(name='app.tasks.fetch_and_process_drones')
def fetch_and_process_drones():
    """
    Celery task entry point: fetches, processes, and records drone violations.
    """
    try:
        drones = fetch_drones()
        logger.info("Fetched %d drones", len(drones))
    except httpx.HTTPStatusError as e:
        logger.error("Drone API error: %s", e.response.status_code)
        return
    except httpx.RequestError as e:
        logger.error("Network error fetching drones: %s", e)
        return
    except ValueError as e:
        logger.error("Invalid JSON from drone API: %s", e)
        return
    except Exception as e:
        logger.exception("Unexpected fetch error: %s", e)
        return

    db = SessionLocal()
    try:
        total, new_violations = process_drones(drones, db)
        try:
            db.commit()
        except SQLAlchemyError as e:
            logger.error("Commit failed: %s", e)
            db.rollback()
        return {"processed": total, "new_violations": new_violations}
    except Exception as e:
        logger.exception("Unhandled processing error: %s", e)
        db.rollback()
    finally:
        db.close()
