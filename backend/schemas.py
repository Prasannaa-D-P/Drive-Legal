from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class TrafficRuleBase(BaseModel):
    id: str
    section: str
    name: str
    category: str
    description: Optional[str] = None
    base_fines: Dict[str, int]
    repeat_fines: Optional[Dict[str, int]] = None
    penalties: Optional[str] = None
    court_only: bool = False

    class Config:
        from_attributes = True

class StateOverrideBase(BaseModel):
    state_code: str
    violation_id: str
    fine_amount: Dict[str, int]

    class Config:
        from_attributes = True

class VehicleBase(BaseModel):
    vehicle_number: str
    vehicle_type: str
    owner_name: str
    registration_date: Optional[str] = None

    class Config:
        from_attributes = True

class ChallanItemBase(BaseModel):
    violation_id: Optional[str] = None
    section: str
    description: str
    fine_amount: int

    class Config:
        from_attributes = True

class ChallanBase(BaseModel):
    challan_number: str
    vehicle_number: str
    state_code: str
    violation_date: str
    total_amount: int
    status: str
    items: List[ChallanItemBase]

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
    state_code: Optional[str] = None
    state_name: Optional[str] = None
    emergency_contacts: Dict[str, str] = {}
    local_rules: List[str] = []

class ChallanSaveRequest(BaseModel):
    state_code: str
    vehicle_type: str
    violations: List[str] # List of violation IDs
    is_repeat: bool = False

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
