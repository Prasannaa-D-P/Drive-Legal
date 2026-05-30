import random
import uuid
import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Challan, State, Violation, ViolationPenalty, TrafficRule
from backend.schemas import RTOChallanLookupResponse, ChallanSaveRequest
from backend.services.rto_api import fetch_rto_challans
from backend.services.ocr_reader import read_challan_receipt

router = APIRouter(
    prefix="/challan",
    tags=["Challan Management"]
)

@router.get("/lookup/{vehicle_number}", response_model=RTOChallanLookupResponse)
def lookup_challan(vehicle_number: str, db: Session = Depends(get_db)):
    result = fetch_rto_challans(vehicle_number, db)
    return result

@router.post("/upload-receipt")
async def upload_ocr_receipt(file: UploadFile = File(...)):
    contents = await file.read()
    filename = file.filename
    ocr_result = read_challan_receipt(contents, filename)
    return ocr_result

@router.post("/save")
def save_calculated_challan(payload: ChallanSaveRequest, db: Session = Depends(get_db)):
    """
    Saves a compiled client challan calculation to the database and returns a unique receipt number.
    """
    random_digits = "".join([str(random.randint(0, 9)) for _ in range(8)])
    challan_no = f"DL{random_digits}"
    
    state = db.query(State).filter(State.state_code.ilike(payload.state_code)).first()
    state_id = state.state_id if state else None
    
    v_type_id = "car"
    if payload.vehicle_type == "two_wheeler":
        v_type_id = "2w"
    elif payload.vehicle_type == "three_wheeler":
        v_type_id = "3w"
    elif payload.vehicle_type == "lmv":
        v_type_id = "car"
    elif payload.vehicle_type == "hgv":
        v_type_id = "bus"
    else:
        v_type_id = payload.vehicle_type
        
    total_amount = 0
    violation_names = []
    sections = []
    consequences_list = []
    
    for violation_id in payload.violations:
        violation = db.query(Violation).filter(Violation.violation_id == violation_id).first()
        if not violation:
            continue
            
        violation_names.append(violation.violation_name)
        
        penalty = db.query(ViolationPenalty).filter(
            ViolationPenalty.violation_id == violation_id,
            ViolationPenalty.vehicle_type_id == v_type_id,
            ViolationPenalty.state_id == state_id
        ).first()
        
        if not penalty and state_id:
            penalty = db.query(ViolationPenalty).filter(
                ViolationPenalty.violation_id == violation_id,
                ViolationPenalty.vehicle_type_id == v_type_id
            ).first()
            
        fine = 1000
        if penalty:
            if payload.is_repeat:
                fine = penalty.repeat_offense_fine or penalty.second_offense_fine or (penalty.first_offense_fine * 2)
            else:
                fine = penalty.first_offense_fine or 1000
            
            if penalty.imprisonment:
                consequences_list.append(f"{violation.violation_name}: {penalty.imprisonment}")
            if penalty.license_points:
                consequences_list.append(f"{violation.violation_name}: +{penalty.license_points} License Points")
                
        total_amount += fine
        
        rule = db.query(TrafficRule).filter(TrafficRule.category == violation.category).first()
        if rule and rule.section_reference:
            sections.append(rule.section_reference)
        else:
            sections.append("Section 177")
            
    surcharge = len(payload.violations) * 100
    total_amount += surcharge
    
    issued_time = int(time.time() * 1000)
    deadline_time = issued_time + (60 * 24 * 3600 * 1000) # 60 days
    
    challan = Challan(
        id=str(uuid.uuid4()),
        challan_number=challan_no,
        vehicle_number="CALCULATOR_SAVE",
        violation_name=", ".join(violation_names) if violation_names else "Multiple Violations",
        location=f"{(state.state_name if state else payload.state_code.upper())} Highway Guard",
        amount=total_amount,
        status="Unpaid",
        issued_at=issued_time,
        deadline_at=deadline_time,
        section=", ".join(list(set(sections))) if sections else "Section 177",
        act="Motor Vehicles Act 2019",
        consequences="; ".join(consequences_list) if consequences_list else "Fine payment pending"
    )
    db.add(challan)
    db.commit()
    db.refresh(challan)
    
    print(f"[Backend] Saved calculator challan receipt: {challan_no} (Rs. {total_amount})")
    
    return {
        "status": "success",
        "challan_number": challan_no,
        "total_amount": total_amount,
        "violation_date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
