from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from .database import Base

class TrafficRule(Base):
    __tablename__ = "traffic_rules"

    id = Column(String, primary_key=True, index=True)
    section = Column(String, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    base_fines = Column(JSON, nullable=False) # JSON structure mapping vehicle classes -> amounts
    repeat_fines = Column(JSON, nullable=True)
    penalties = Column(Text, nullable=True)
    court_only = Column(Boolean, default=False)

    # Relationships
    overrides = relationship("StateOverride", back_populates="rule", cascade="all, delete-orphan")


class StateOverride(Base):
    __tablename__ = "state_overrides"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    state_code = Column(String, nullable=False, index=True) # e.g. "DL", "KA"
    violation_id = Column(String, ForeignKey("traffic_rules.id", ondelete="CASCADE"), nullable=False)
    fine_amount = Column(JSON, nullable=False) # JSON mapping vehicle classes -> state-specific amounts

    # Relationships
    rule = relationship("TrafficRule", back_populates="overrides")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_number = Column(String, unique=True, index=True, nullable=False) # e.g. "DL3CA1234"
    vehicle_type = Column(String, nullable=False) # e.g. "two_wheeler", "lmv"
    owner_name = Column(String, nullable=False)
    registration_date = Column(String, nullable=True)


class Challan(Base):
    __tablename__ = "challans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    challan_number = Column(String, unique=True, index=True, nullable=False) # e.g. "DL0009230489"
    vehicle_number = Column(String, index=True, nullable=False)
    state_code = Column(String, nullable=False) # e.g. "DL", "KA"
    violation_date = Column(String, nullable=False) # e.g. "2026-05-29 14:30"
    total_amount = Column(Integer, default=0)
    status = Column(String, default="Unpaid") # "Unpaid", "Paid", "In Court"

    # Relationships
    items = relationship("ChallanItem", back_populates="challan", cascade="all, delete-orphan")


class ChallanItem(Base):
    __tablename__ = "challan_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    challan_id = Column(Integer, ForeignKey("challans.id", ondelete="CASCADE"), nullable=False)
    violation_id = Column(String, nullable=True) # Matches TrafficRule.id if known
    section = Column(String, nullable=False)
    description = Column(String, nullable=False)
    fine_amount = Column(Integer, nullable=False)

    # Relationships
    challan = relationship("Challan", back_populates="items")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True) # e.g. UUID string
    created_at = Column(String, nullable=False)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String, nullable=False) # 'user' or 'bot'
    text = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
