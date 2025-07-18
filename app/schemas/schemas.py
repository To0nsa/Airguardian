# app/schemas.py

from pydantic import BaseModel
from typing import List

# ========== Health Schemas =========

class HealthOut(BaseModel):
    success: str

    class Config:
        schema_extra = {
            "example": {"success": "ok"}
        }

# ========== Drone Schemas ==========

class DroneOut(BaseModel):
    id: str
    x: float
    y: float
    z: float
    owner_id: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "eab0e389-7262-4ec7-8d56-9a468d671f5b",
                "x": 123.45,
                "y": -321.0,
                "z": 200.0,
                "owner_id": "add6ad16-c284-4304-a0e4-1cc39052adc3"
            }
        }

# ========== Violation Schemas ==========

class Position(BaseModel):
    x: float
    y: float
    z: float

class OwnerInfo(BaseModel):
    first: str
    last: str
    ssn: str
    phone: str

class ViolationOut(BaseModel):
    drone_id: str
    timestamp: str  # ISO8601 string, e.g. "2025-07-18T09:41:36.017Z"
    position: Position
    owner: OwnerInfo

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "drone_id": "eab0e389-7262-4ec7-8d56-9a468d671f5b",
                "timestamp": "2025-07-18T09:41:36.017Z",
                "position": {"x": 123.45, "y": -321.0, "z": 200.0},
                "owner": {
                    "first": "John",
                    "last": "Doe",
                    "ssn": "010101-123A",
                    "phone": "+358401234567"
                }
            }
        }

# ========== Lists for responses ==========

DronesList = List[DroneOut]
ViolationsList = List[ViolationOut]
