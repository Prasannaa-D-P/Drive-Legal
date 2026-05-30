from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
import time
from backend.database import get_db
from backend.models import (
    State, Country, City, ViolationPenalty, VehicleType, Violation, 
    TrafficRule, SyncQueue, ChallanCalculation, Profile, Vehicle, 
    Challan, Notification
)
from backend.schemas import (
    SyncRequest, CalculateRequest, ProfileRequest, ProfileResponse, 
    NotificationBase
)

router = APIRouter(
    tags=["General Utilities"]
)

@router.get("/states")
def get_states(db: Session = Depends(get_db)):
    results = (
        db.query(
            State.state_code.label("code"),
            State.state_name.label("name"),
            func.count(ViolationPenalty.penalty_id).label("rules_count")
        )
        .join(Country, State.country_id == Country.country_id)
        .outerjoin(ViolationPenalty, State.state_id == ViolationPenalty.state_id)
        .filter(Country.country_code == "IN")
        .group_by(State.state_id, State.state_code, State.state_name)
        .all()
    )
    
    # Fallback to defaults if database is not seeded
    if not results:
        return [
            {"code": "TN", "name": "Tamil Nadu", "rules_count": 12},
            {"code": "MH", "name": "Maharashtra", "rules_count": 12},
            {"code": "DL", "name": "New Delhi", "rules_count": 12}
        ]
        
    return [{"code": r.code, "name": r.name, "rules_count": r.rules_count} for r in results]


@router.get("/cities")
def get_cities(state_code: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(City.city_name.label("name"), State.state_code.label("state")).join(State, City.state_id == State.state_id)
    if state_code:
        query = query.filter(func.upper(State.state_code) == state_code.upper())
    results = query.all()
    return [{"name": r.name, "state": r.state} for r in results]


@router.get("/categories")
def get_categories():
    return ["Speed", "Parking", "Documents", "Safety", "DUI", "General"]


@router.post("/sync")
def sync_offline_logs(payload: SyncRequest, db: Session = Depends(get_db)):
    inserted_count = 0
    for log in payload.logs:
        # SyncQueue item
        queue_item = SyncQueue(
            device_id=payload.device_id,
            violation_id=log.violation_id,
            state_code=log.state_code,
            vehicle_type=log.vehicle_type,
            fine_amount=log.fine_amount,
            timestamp=log.timestamp
        )
        db.add(queue_item)
        
        # State mapping
        state = db.query(State).filter(func.upper(State.state_code) == log.state_code.upper()).first()
        state_id = state.state_id if state else "state_mh"
        
        # Vehicle Type mapping
        vtype = db.query(VehicleType).filter(
            (VehicleType.vehicle_name.ilike(f"%{log.vehicle_type}%")) | 
            (VehicleType.vehicle_type_id == log.vehicle_type.lower()[:3])
        ).first()
        vtype_id = vtype.vehicle_type_id if vtype else "car"
        
        # Challan Calculation log
        calc = ChallanCalculation(
            calculation_id=str(uuid.uuid4()),
            vehicle_type_id=vtype_id,
            violation_id=log.violation_id,
            state_id=state_id,
            offense_number=1,
            calculated_fine=log.fine_amount
        )
        db.add(calc)
        inserted_count += 1
        
    db.commit()
    return {
        "status": "success",
        "synced_count": inserted_count,
        "last_sync_at": int(time.time())
    }


@router.post("/calculate")
def calculate_fine(req: CalculateRequest, db: Session = Depends(get_db)):
    # 1. Resolve State
    state = db.query(State).filter(func.upper(State.state_code) == req.state_code.upper()).first()
    if not state:
        state = db.query(State).filter(State.state_code == "MH").first()
    state_id = state.state_id if state else "state_mh"
    state_name = state.state_name if state else "Maharashtra"
    
    # 2. Resolve Vehicle Type
    vtype = db.query(VehicleType).filter(
        (VehicleType.vehicle_type_id == req.vehicle_type_id) | 
        (VehicleType.vehicle_name.ilike(f"%{req.vehicle_type_id}%"))
    ).first()
    if not vtype:
        vtype = db.query(VehicleType).filter(VehicleType.vehicle_type_id == "car").first()
    v_type_id = vtype.vehicle_type_id if vtype else "car"
    v_name = vtype.vehicle_name if vtype else "Light Motor Vehicle (LMV)"
    
    # 3. Retrieve Penalty Details
    penalty = db.query(ViolationPenalty).filter(
        ViolationPenalty.violation_id == req.violation_id,
        ViolationPenalty.vehicle_type_id == v_type_id,
        ViolationPenalty.state_id == state_id
    ).first()
    
    # Fallback to default state (MH) if state-specific not found
    if not penalty:
        mh_state = db.query(State).filter(State.state_code == "MH").first()
        if mh_state:
            penalty = db.query(ViolationPenalty).filter(
                ViolationPenalty.violation_id == req.violation_id,
                ViolationPenalty.vehicle_type_id == v_type_id,
                ViolationPenalty.state_id == mh_state.state_id
            ).first()
            
    if not penalty:
        raise HTTPException(status_code=404, detail="Penalty configuration not found.")
        
    # Determine base fine amount
    if req.offense_number == 1:
        base_fine = penalty.first_offense_fine or 1000
    elif req.offense_number == 2:
        base_fine = penalty.second_offense_fine or penalty.repeat_offense_fine or 2000
    else:
        base_fine = penalty.repeat_offense_fine or 2000
        
    # Get Violation name
    violation = db.query(Violation).filter(Violation.violation_id == req.violation_id).first()
    violation_name = violation.violation_name if violation else "Traffic Violation"
    category = violation.category if violation else "general"
    
    # Get Section reference
    rule = db.query(TrafficRule).filter(TrafficRule.category == category, TrafficRule.state_id == state_id).first()
    section_ref = rule.section_reference if rule else "Section 177"
    
    surcharge = 100 if category in ["speed", "parking"] else 0
    total_fine = base_fine + surcharge
    
    # Log calculation
    calc_id = str(uuid.uuid4())
    calc = ChallanCalculation(
        calculation_id=calc_id,
        vehicle_type_id=v_type_id,
        violation_id=req.violation_id,
        state_id=state_id,
        offense_number=req.offense_number,
        calculated_fine=total_fine
    )
    db.add(calc)
    db.commit()
    
    return {
        "calculation_id": calc_id,
        "violation_id": req.violation_id,
        "violation_name": violation_name,
        "vehicle_type": v_name,
        "state_code": req.state_code,
        "state_name": state_name,
        "is_repeat": req.offense_number > 1,
        "base_fine": base_fine,
        "surcharge": surcharge,
        "compounding_fee": base_fine,
        "total_fine": total_fine,
        "licence_points": penalty.license_points or 0,
        "imprisonment": penalty.imprisonment or "No imprisonment",
        "section": section_ref,
        "act": "Motor Vehicles Act 2019",
        "vehicle_seizure": bool(penalty.vehicle_seizure),
        "calculated_at": int(time.time() * 1000)
    }


@router.get("/profile/{device_id}", response_model=ProfileResponse)
def get_profile(device_id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.device_id == device_id).first()
    if not profile:
        profile = Profile(
            device_id=device_id,
            name="Mock Driver",
            email="",
            phone="",
            safety_score=85,
            country="IN",
            state_code="MH",
            city="Mumbai"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
    vehicles = db.query(Vehicle).filter(Vehicle.device_id == device_id).all()
    return {
        "device_id": profile.device_id,
        "name": profile.name,
        "email": profile.email,
        "phone": profile.phone,
        "safety_score": profile.safety_score,
        "country": profile.country,
        "state_code": profile.state_code,
        "city": profile.city,
        "vehicles": vehicles
    }


@router.post("/profile/{device_id}")
def update_profile(device_id: str, payload: ProfileRequest, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.device_id == device_id).first()
    if not profile:
        profile = Profile(device_id=device_id)
        db.add(profile)
    profile.name = payload.name
    profile.email = payload.email
    profile.phone = payload.phone
    profile.safety_score = payload.safety_score
    profile.country = payload.country
    profile.state_code = payload.state_code
    profile.city = payload.city
    
    # Delete existing vehicles and insert new ones
    db.query(Vehicle).filter(Vehicle.device_id == device_id).delete()
    for v in payload.vehicles:
        vehicle = Vehicle(
            id=v.id,
            device_id=device_id,
            name=v.name,
            type=v.type,
            registration_state=v.registration_state,
            registration_number=v.registration_number
        )
        db.add(vehicle)
    db.commit()
    return {"status": "success"}


@router.get("/user/challans")
def get_user_challans(plate: str, db: Session = Depends(get_db)):
    clean_plate = plate.upper().replace(" ", "").replace("-", "")
    challans = db.query(Challan).all()
    
    matched_challans = []
    for c in challans:
        if c.vehicle_number.upper().replace(" ", "").replace("-", "") == clean_plate:
            matched_challans.append({
                "id": c.id,
                "challanNumber": c.challan_number,
                "vehicleNumber": c.vehicle_number,
                "violationName": c.violation_name,
                "location": c.location,
                "amount": c.amount,
                "status": c.status,
                "issuedAt": c.issued_at,
                "deadlineAt": c.deadline_at,
                "section": c.section,
                "act": c.act,
                "consequences": c.consequences
            })
    return {"challans": matched_challans}


@router.get("/notifications", response_model=List[NotificationBase])
def get_notifications(db: Session = Depends(get_db)):
    return db.query(Notification).order_by(Notification.timestamp.desc()).all()


@router.post("/notifications/{id}/read")
def mark_notification_read(id: str, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == id).first()
    if notif:
        notif.read = 1
        db.commit()
    return {"status": "success"}


@router.post("/notifications/mark-all-read")
def mark_all_notifications_read(db: Session = Depends(get_db)):
    db.query(Notification).update({Notification.read: 1})
    db.commit()
    return {"status": "success"}


@router.post("/notifications/clear-all")
def clear_all_notifications(db: Session = Depends(get_db)):
    db.query(Notification).delete()
    db.commit()
    return {"status": "success"}
