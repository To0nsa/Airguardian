#app/db/models.py
# This file defines the SQLAlchemy models for the Airguardian project.
# Each model corresponds to a table in the database, and they inherit from Base.

from sqlalchemy import Column, String, Float, DateTime
from app.db.base import Base

class Violation(Base):
    __tablename__ = "violations"

    id = Column(String, primary_key=True)
    drone_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, nullable=False)
    owner_first = Column(String, nullable=False)
    owner_last = Column(String, nullable=False)
    owner_ssn = Column(String, nullable=False)
    owner_phone = Column(String, nullable=False)

class NFZActive(Base):
    __tablename__ = "nfz_active"
    drone_id = Column(String, primary_key=True, index=True)