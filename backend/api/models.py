from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="SOC Analyst")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    severity = Column(String) # critical, high, medium, low
    name = Column(String)
    src_ip = Column(String)
    dst_ip = Column(String)
    mitre_tactic = Column(String)
    confidence = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True) # e.g. INC-2024-001
    title = Column(String)
    severity = Column(String)
    status = Column(String) # open, investigating, resolved
    assignee = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ThreatCampaign(Base):
    __tablename__ = "threats"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    severity = Column(String)
    mitre_tag = Column(String)
    description = Column(String)
    confidence = Column(Integer)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
