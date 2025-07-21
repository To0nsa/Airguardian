# app/db/models.py
"""
SQLAlchemy ORM models for the Airguardian project.
Defines the database tables and relationships for Owners, Drones,
Violations, and No-Fly Zones active.
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Owner(Base):
    """
    Represents the owner of drones. Each owner can have multiple drones and violations.
    """
    __tablename__ = "owners"

    # Primary key: unique integer ID for each owner
    id = Column(Integer, primary_key=True)

    # Personal details for the owner
    first_name             = Column(String, nullable=False)
    last_name              = Column(String, nullable=False)
    email                  = Column(String, nullable=False)
    phone_number           = Column(String, nullable=False)
    social_security_number = Column(String, nullable=False)
    purchased_at           = Column(String, nullable=False)

    # Relationships
    # An owner can have multiple drones
    drones = relationship("Drone", back_populates="owner")
    # An owner can appear in multiple violations
    violations = relationship("Violation", back_populates="owner")
    # An owner can have multiple active NFZ breaches
    nfz_actives = relationship("NFZActive", back_populates="owner")


class Drone(Base):
    """
    Represents a drone. Contains location coordinates and a link to its owner.
    """
    __tablename__ = "drones"

    # UUID primary key for each drone
    id = Column(PGUUID(as_uuid=True), primary_key=True)

    # Foreign key linking this drone to an owner
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)

    # Current or recorded coordinates of the drone
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    z = Column(Integer, nullable=False)

    # Relationships
    # Access the Owner object via drone.owner
    owner = relationship("Owner", back_populates="drones")
    # All violations associated with this drone
    violations = relationship("Violation", back_populates="drone")
    # reverse relationship needed for NFZActive
    nfz_actives = relationship("NFZActive", back_populates="drone")


class Violation(Base):
    """
    Represents a flight violation by a drone, including timestamp and position data.
    Linked to both Drone and Owner for nested output.
    """
    __tablename__ = "violations"

    # Auto-incrementing primary key for each violation record
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys linking to drone and owner tables
    drone_id = Column(PGUUID(as_uuid=True), ForeignKey("drones.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)

    # When the violation occurred
    timestamp = Column(DateTime, nullable=False)

    # Position of the drone at the time of violation
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    z = Column(Integer, nullable=False)

    # Relationships for nested attribute access
    # Access the Drone object via violation.drone
    drone = relationship("Drone", back_populates="violations")
    # Access the Owner object via violation.owner
    owner = relationship("Owner", back_populates="violations")

class NFZActive(Base):
    """
    Represents an active No-Fly Zone (NFZ) breach entry for a drone.
    Links directly to both Drone and Owner for quick lookups.
    """
    __tablename__ = "nfz_active"

    # Foreign key to the Drone table, used as primary key for this record
    drone_id = Column(PGUUID(as_uuid=True), ForeignKey("drones.id"), primary_key=True, index=True)
    # Foreign key to the Owner table for the same drone's owner
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)

    # Relationships
    drone = relationship("Drone",    back_populates="nfz_actives")
    owner = relationship("Owner",    back_populates="nfz_actives")