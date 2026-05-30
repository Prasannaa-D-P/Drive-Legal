import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db
from backend.models import Challan, ChallanItem, TrafficRule
from backend.schemas import RTOChallanLookupResponse, ChallanSaveRequest
from backend.services.rto_api import fetch_rto_challans
from backend.services.ocr_reader import read_challan_receipt

router = APIRouter(
    prefix="/challan",
    tags=["Challan Management"]
)

@router.get("/lookup/{vehicle_number}", response_model=RTOChallanLookupResponse)
def lookup_challan(vehicle_number: str, db: Session = Depends(get_db)):
    # Sanitize and perform RTO database query (with eager-loaded items)
    result = fetch_rto_challans(vehicle_number, db)
    # Eagerly reload challans with items to satisfy Pydantic response model
    if result.get("challans"):
        challan_ids = [c.id for c in result["challans"]]
        result["challans"] = (
            db.query(Challan)
            .options(joinedload(Challan.items))
            .filter(Challan.id.in_(challan_ids))
            .all()
        )
    return result

@router.post("/upload-receipt")
async def upload_ocr_receipt(file: UploadFile = File(...)):
    # Read file bytes
    contents = await file.read()
    filename = file.filename
    
    # Process OCR reading
    ocr_result = read_challan_receipt(contents, filename)
    return ocr_result

@router.post("/save")
def save_calculated_challan(payload: ChallanSaveRequest, db: Session = Depends(get_db)):
    """
    Saves a compiled client challan calculation to the database and returns a unique receipt number.
    """
    # Create random Challan ID
    random_digits = "".join([str(random.randint(0, 9)) for _ in range(8)])
    challan_no = f"DL{random_digits}"
    
    # Calculate subtotal and build items list
    total_amount = 0
    items = []
    
    for violation_id in payload.violations:
        rule = db.query(TrafficRule).filter(TrafficRule.id == violation_id).first()
        if not rule:
            continue
            
        fine = rule.base_fines.get(payload.vehicle_type, 0)
        
        # Multiply if repeat offense
        if payload.is_repeat:
            fine = rule.repeat_fines.get(payload.vehicle_type, fine * 2) if rule.repeat_fines else fine * 2
            
        total_amount += fine
        
        items.append({
            "violation_id": violation_id,
            "section": rule.section,
            "description": f"Compounded violation: {rule.name}",
            "fine_amount": fine
        })
        
    # Surcharge
    surcharge = len(payload.violations) * 100
    total_amount += surcharge
    
    # Save Challan record
    challan = Challan(
        challan_number=challan_no,
        vehicle_number="CALCULATOR_SAVE",
        state_code=payload.state_code,
        violation_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        total_amount=total_amount,
        status="Unpaid"
    )
    db.add(challan)
    db.flush()
    
    # Save items
    for item in items:
        db_item = ChallanItem(
            challan_id=challan.id,
            violation_id=item["violation_id"],
            section=item["section"],
            description=item["description"],
            fine_amount=item["fine_amount"]
        )
        db.add(db_item)
        
    db.commit()
    print(f"[Backend] Saved calculator challan receipt: {challan_no} (Rs. {total_amount})")
    
    return {
        "status": "success",
        "challan_number": challan_no,
        "total_amount": total_amount,
        "violation_date": challan.violation_date
    }
