from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime, Text, Numeric, Date, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class Tourist(Base):
    __tablename__ = "tourists"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    contact = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=True)
    trip_info = Column(JSON, default={})
    emergency_contact = Column(String, nullable=False)
    safety_score = Column(Integer, default=100, nullable=False)
    age = Column(Integer, nullable=True)
    nationality = Column(String, default="Indian")
    passport_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    last_location_update = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    locations = relationship("Location", back_populates="tourist", cascade="all, delete-orphan")
    location_history = relationship("LocationHistory", back_populates="tourist", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="tourist", cascade="all, delete-orphan")
    ai_assessments = relationship("AIAssessment", back_populates="tourist", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tourist(id={self.id}, name='{self.name}', safety_score={self.safety_score})>"