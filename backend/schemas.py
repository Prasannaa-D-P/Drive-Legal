from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

# 1. Countries
class CountryBase(BaseModel):
    country_id: str
    country_code: str
    country_name: str
    class Config:
        from_attributes = True

# 2. States
class StateBase(BaseModel):
    state_id: str
    country_id: str
    state_code: str
    state_name: str
    class Config:
        from_attributes = True

# 3. Cities
class CityBase(BaseModel):
    city_id: str
    state_id: str
    city_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    class Config:
        from_attributes = True

# 4. Traffic Rules
class TrafficRuleBase(BaseModel):
    rule_id: str
    country_id: str
    state_id: str
    city_id: Optional[str] = None
    category: str
    rule_title: str
    rule_description: str
    section_reference: Optional[str] = None
    effective_date: Optional[str] = None
    source_url: Optional[str] = None
    class Config:
        from_attributes = True

# 5. Vehicle Types
class VehicleTypeBase(BaseModel):
    vehicle_type_id: str
    vehicle_name: str
    description: Optional[str] = None
    class Config:
        from_attributes = True

# 6. Violations
class ViolationBase(BaseModel):
    violation_id: str
    violation_name: str
    category: str
    description: str
    class Config:
        from_attributes = True

# 7. Violation Penalties
class ViolationPenaltyBase(BaseModel):
    penalty_id: str
    violation_id: str
    vehicle_type_id: str
    country_id: str
    state_id: str
    city_id: Optional[str] = None
    first_offense_fine: Optional[int] = None
    second_offense_fine: Optional[int] = None
    repeat_offense_fine: Optional[int] = None
    imprisonment: Optional[str] = None
    license_points: int = 0
    vehicle_seizure: bool = False
    effective_date: Optional[str] = None
    class Config:
        from_attributes = True

# 8. Challan Calculations
class ChallanCalculationBase(BaseModel):
    calculation_id: str
    vehicle_type_id: str
    violation_id: str
    state_id: str
    city_id: Optional[str] = None
    offense_number: int
    calculated_fine: int
    class Config:
        from_attributes = True

# 9. FAQ Knowledge
class FAQKnowledgeBase(BaseModel):
    faq_id: str
    country_id: str
    state_id: str
    city_id: Optional[str] = None
    question: str
    answer: str
    category: Optional[str] = None
    class Config:
        from_attributes = True

# 10. Sync Versions
class SyncVersionBase(BaseModel):
    version_id: str
    data_type: str
    version_number: str
    checksum: Optional[str] = None
    class Config:
        from_attributes = True

# 11. Legal Sources
class LegalSourceBase(BaseModel):
    source_id: str
    country_id: str
    state_id: str
    source_name: str
    source_url: Optional[str] = None
    document_title: Optional[str] = None
    publication_date: Optional[str] = None
    class Config:
        from_attributes = True

# --- Compatibility models for Web & Mobile Clients ---

class ProfileVehicleItem(BaseModel):
    id: str
    name: str
    type: str
    registration_state: Optional[str] = None
    registration_number: Optional[str] = None
    class Config:
        from_attributes = True

class ProfileRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    safety_score: int = 85
    country: str = "IN"
    state_code: str = "MH"
    city: str = "Mumbai"
    vehicles: List[ProfileVehicleItem]

class ProfileResponse(BaseModel):
    device_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    safety_score: int
    country: str
    state_code: str
    city: str
    vehicles: List[ProfileVehicleItem]
    class Config:
        from_attributes = True

class SyncItem(BaseModel):
    device_id: str
    violation_id: str
    state_code: str
    vehicle_type: str
    fine_amount: int
    timestamp: int

class SyncRequest(BaseModel):
    device_id: str
    logs: List[SyncItem]

class CalculateRequest(BaseModel):
    violation_id: str
    vehicle_type_id: str
    state_code: str
    offense_number: int = 1
    city_name: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    state_code: Optional[str] = "MH"
    language: Optional[str] = "en"

class ChallanBase(BaseModel):
    id: str
    challan_number: str
    vehicle_number: str
    violation_name: str
    location: str
    amount: int
    status: str
    issued_at: int
    deadline_at: int
    section: str
    act: str
    consequences: str
    class Config:
        from_attributes = True

class NotificationBase(BaseModel):
    id: str
    type: str
    title: str
    body: str
    read: int
    timestamp: int
    class Config:
        from_attributes = True

# Chat Bot Cache Models (ChatMessage, ChatSession)
class ChatMessageCreate(BaseModel):
    session_id: str
    sender: str
    text: str
    timestamp: str

class ChatMessageBase(BaseModel):
    id: int
    session_id: str
    sender: str
    text: str
    timestamp: str
    class Config:
        from_attributes = True

class ChatSessionBase(BaseModel):
    id: str
    created_at: str
    messages: List[ChatMessageBase] = []
    class Config:
        from_attributes = True

# Challan save requests
class ChallanSaveRequest(BaseModel):
    state_code: str
    vehicle_type: str
    violations: List[str] # List of violation IDs
    is_repeat: bool = False

# RTO Lookup Response
class VehicleBase(BaseModel):
    vehicle_number: str
    vehicle_type: str
    owner_name: str
    registration_date: Optional[str] = None
    class Config:
        from_attributes = True

class RTOChallanLookupResponse(BaseModel):
    vehicle: Optional[VehicleBase] = None
    challans: List[ChallanBase] = []

class GeoRequest(BaseModel):
    latitude: float
    longitude: float

class GeoResponse(BaseModel):
    matched: bool
    state_code: str
    state_name: str
    emergency_contacts: Dict[str, str]
    local_rules: List[str]

