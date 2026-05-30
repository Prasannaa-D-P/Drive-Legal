from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# 1. Countries Table
class Country(Base):
    __tablename__ = "countries"

    country_id = Column(String, primary_key=True) # UUID
    country_code = Column(String(5), unique=True, nullable=False) # e.g. "IN", "US"
    country_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 2. States / Regions Table
class State(Base):
    __tablename__ = "states"

    state_id = Column(String, primary_key=True) # UUID
    country_id = Column(String, ForeignKey("countries.country_id", ondelete="CASCADE"), nullable=False)
    state_code = Column(String(10), nullable=False) # e.g. "MH", "TN", "DL"
    state_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 3. Cities Table
class City(Base):
    __tablename__ = "cities"

    city_id = Column(String, primary_key=True) # UUID
    state_id = Column(String, ForeignKey("states.state_id", ondelete="CASCADE"), nullable=False)
    city_name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 4. Traffic Rules Table
class TrafficRule(Base):
    __tablename__ = "traffic_rules"

    rule_id = Column(String, primary_key=True) # UUID
    country_id = Column(String, ForeignKey("countries.country_id", ondelete="CASCADE"), nullable=False)
    state_id = Column(String, ForeignKey("states.state_id", ondelete="CASCADE"), nullable=False)
    city_id = Column(String, ForeignKey("cities.city_id", ondelete="SET NULL"), nullable=True)
    category = Column(String(50), nullable=False) # e.g. "Speed", "DUI", "Safety"
    rule_title = Column(String, nullable=False)
    rule_description = Column(Text, nullable=False)
    section_reference = Column(String(100), nullable=True) # e.g. "Section 129"
    effective_date = Column(String, nullable=True)
    source_url = Column(Text, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 5. Vehicle Types Table
class VehicleType(Base):
    __tablename__ = "vehicle_types"

    vehicle_type_id = Column(String, primary_key=True) # e.g. "2w", "car"
    vehicle_name = Column(String(50), nullable=False) # e.g. "Two-Wheeler", "LMV"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# 6. Violations Table
class Violation(Base):
    __tablename__ = "violations"

    violation_id = Column(String, primary_key=True) # e.g. "speeding"
    violation_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 7. Violation Penalties Table (MOST IMPORTANT)
class ViolationPenalty(Base):
    __tablename__ = "violation_penalties"

    penalty_id = Column(String, primary_key=True) # UUID
    violation_id = Column(String, ForeignKey("violations.violation_id", ondelete="CASCADE"), nullable=False)
    vehicle_type_id = Column(String, ForeignKey("vehicle_types.vehicle_type_id", ondelete="CASCADE"), nullable=False)
    country_id = Column(String, ForeignKey("countries.country_id", ondelete="CASCADE"), nullable=False)
    state_id = Column(String, ForeignKey("states.state_id", ondelete="CASCADE"), nullable=False)
    city_id = Column(String, ForeignKey("cities.city_id", ondelete="SET NULL"), nullable=True)
    first_offense_fine = Column(Integer, nullable=True)
    second_offense_fine = Column(Integer, nullable=True)
    repeat_offense_fine = Column(Integer, nullable=True)
    imprisonment = Column(String(100), nullable=True)
    license_points = Column(Integer, default=0)
    vehicle_seizure = Column(Boolean, default=False)
    effective_date = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 8. Challan Calculator Logs
class ChallanCalculation(Base):
    __tablename__ = "challan_calculations"

    calculation_id = Column(String, primary_key=True) # UUID
    vehicle_type_id = Column(String, ForeignKey("vehicle_types.vehicle_type_id", ondelete="CASCADE"), nullable=False)
    violation_id = Column(String, ForeignKey("violations.violation_id", ondelete="CASCADE"), nullable=False)
    state_id = Column(String, ForeignKey("states.state_id", ondelete="CASCADE"), nullable=False)
    city_id = Column(String, ForeignKey("cities.city_id", ondelete="SET NULL"), nullable=True)
    offense_number = Column(Integer, nullable=False) # 1, 2, 3...
    calculated_fine = Column(Integer, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)


# 9. AI Chatbot Knowledge Base
class FAQKnowledge(Base):
    __tablename__ = "faq_knowledge"

    faq_id = Column(String, primary_key=True) # UUID
    country_id = Column(String, ForeignKey("countries.country_id", ondelete="CASCADE"), nullable=False)
    state_id = Column(String, ForeignKey("states.state_id", ondelete="CASCADE"), nullable=False)
    city_id = Column(String, ForeignKey("cities.city_id", ondelete="SET NULL"), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 10. Offline Sync Management
class SyncVersion(Base):
    __tablename__ = "sync_versions"

    version_id = Column(String, primary_key=True) # UUID
    data_type = Column(String(50), nullable=False) # "rules", "penalties", "faqs", etc.
    version_number = Column(String(20), nullable=False)
    release_date = Column(DateTime, default=datetime.utcnow)
    checksum = Column(String(255), nullable=True)


# 11. Government Sources
class LegalSource(Base):
    __tablename__ = "legal_sources"

    source_id = Column(String, primary_key=True) # UUID
    country_id = Column(String, ForeignKey("countries.country_id", ondelete="CASCADE"), nullable=False)
    state_id = Column(String, ForeignKey("states.state_id", ondelete="CASCADE"), nullable=False)
    source_name = Column(String(200), nullable=False)
    source_url = Column(Text, nullable=True)
    document_title = Column(Text, nullable=True)
    publication_date = Column(String, nullable=True)
    last_verified = Column(DateTime, default=datetime.utcnow)


# --- Backward Compatibility Tables for Web & Mobile Clients ---

# Profile Table
class Profile(Base):
    __tablename__ = "profile"

    device_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    safety_score = Column(Integer, default=85)
    country = Column(String, default="IN")
    state_code = Column(String, default="MH")
    city = Column(String, default="Mumbai")


# Vehicles Table (mapped to Device Profile)
class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String, primary_key=True) # UUID
    device_id = Column(String, ForeignKey("profile.device_id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # e.g. "two_wheeler", "car"
    registration_state = Column(String, nullable=True)
    registration_number = Column(String, nullable=True)


# Challans Table
class Challan(Base):
    __tablename__ = "challans"

    id = Column(String, primary_key=True) # UUID
    challan_number = Column(String, nullable=False)
    vehicle_number = Column(String, nullable=False)
    violation_name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    issued_at = Column(BigInteger, nullable=False)
    deadline_at = Column(BigInteger, nullable=False)
    section = Column(String, nullable=False)
    act = Column(String, nullable=False)
    consequences = Column(Text, nullable=False)


# Notifications Table
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True) # UUID
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    read = Column(Integer, default=0) # 0 for false, 1 for true
    timestamp = Column(BigInteger, nullable=False)


# Sync Queue Table
class SyncQueue(Base):
    __tablename__ = "sync_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, nullable=False)
    violation_id = Column(String, nullable=False)
    state_code = Column(String, nullable=False)
    vehicle_type = Column(String, nullable=False)
    fine_amount = Column(Integer, nullable=False)
    timestamp = Column(BigInteger, nullable=False)


# Chat Sessions (Main API Bot Cache)
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(String, nullable=False)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


# Chat Messages
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)

    session = relationship("ChatSession", back_populates="messages")
