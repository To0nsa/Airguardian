# app/schemas.py
"""Pydantic schemas for Airguardian API responses"""
from pydantic import BaseModel  # BaseModel for Pydantic schemas
from uuid import UUID           # UUID type for drone IDs
from datetime import datetime   # datetime type for timestamps
from typing import List         # List type for collections

# ========== Health Schemas =========

class HealthOut(BaseModel):
    """
    Schema for health check responses.
    """
    status: str

    class Config:
        # Allow reading from ORM objects via attributes
        from_attributes = True
        # Example shown in OpenAPI docs
        json_schema_extra = {
            "example": {
                "success": "ok"
            }
        }

# ========== Position Schema =========

class Position(BaseModel):
    """
    Represents a 3D position with integer coordinates.
    """
    x: int
    y: int
    z: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "x": 123,
                "y": -321,
                "z": 200
            }
        }

# ========== Drone Schemas ==========

class DroneOut(BaseModel):
    """
    Schema for drone data returned by the API.
    """
    id: UUID
    owner_id: int
    x: int
    y: int
    z: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "e6dd6621-c91f-4731-8195-88cf8e88545e",
                "owner_id": 39,
                "x": 8515,
                "y": 9780,
                "z": 216
            }
        }

# ========== Owner Information Schema =========

class OwnerInfo(BaseModel):
    """
    Schema for owner information associated with a violation.
    """
    id: int
    first_name: str
    last_name: str
    email: str
    phone_number: str
    social_security_number: str
    purchased_at: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 12,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone_number": "+358401234567",
                "social_security_number": "010101-123A",
                "purchased_at": "2025-01-01T12:00:00Z"
            }
        }

# ========== Violation Schemas ==========

class ViolationOut(BaseModel):
    """
    Schema for violations, including nested drone and owner info.
    """
    drone: DroneOut          # Nested drone details
    owner: OwnerInfo         # Nested owner details
    timestamp: datetime      # ISO8601 timestamp
    position: Position       # Nested position object

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "drone": {
                    "id": "e6dd6621-c91f-4731-8195-88cf8e88545e",
                    "owner_id": 39,
                    "x": 8515,
                    "y": 9780,
                    "z": 216
                },
                "owner": {
                    "id": 12,
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone_number": "+358401234567",
                    "social_security_number": "010101-123A",
                    "purchased_at": "2025-01-01T12:00:00Z"
                },
                "timestamp": "2025-07-18T09:41:36.017Z",
                "position": {
                    "x": 8515,
                    "y": 9780,
                    "z": 216
                }
            }
        }

# ========== Response List Types =========

# List of drones for endpoints returning multiple drones.
DronesList = List[DroneOut]

# List of violations for endpoints returning multiple violations.
ViolationsList = List[ViolationOut]
