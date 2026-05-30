from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.database import get_db
from backend.models import Violation, ViolationPenalty, State, TrafficRule

router = APIRouter(
    prefix="/rules",
    tags=["Traffic Rules"]
)

@router.get("/")
def read_all_rules(db: Session = Depends(get_db)):
    violations = db.query(Violation).all()
    results = []
    
    # Get state MH as baseline for base fines
    state_mh = db.query(State).filter(State.state_code == "MH").first()
    state_id = state_mh.state_id if state_mh else None

    for v in violations:
        # Fetch penalties for this violation
        penalties = db.query(ViolationPenalty).filter(ViolationPenalty.violation_id == v.violation_id).all()
        
        # Build base_fines dict
        base_fines = {
            "two_wheeler": 0,
            "three_wheeler": 0,
            "lmv": 0,
            "hgv": 0,
            "other": 0
        }
        repeat_fines = {}
        
        # Filter to state MH penalties if available, else first state penalties
        state_penalties = [p for p in penalties if p.state_id == state_id] if state_id else penalties
        if not state_penalties and penalties:
            state_penalties = penalties
            
        for p in state_penalties:
            vtype_key = p.vehicle_type_id
            if vtype_key == "2w":
                vtype_key = "two_wheeler"
            elif vtype_key == "3w":
                vtype_key = "three_wheeler"
            elif vtype_key == "car":
                vtype_key = "lmv"
            elif vtype_key == "bus" or vtype_key == "truck":
                vtype_key = "hgv"
                
            base_fines[vtype_key] = p.first_offense_fine or 0
            if p.repeat_offense_fine or p.second_offense_fine:
                repeat_fines[vtype_key] = p.repeat_offense_fine or p.second_offense_fine or (p.first_offense_fine * 2)
                
        # Find a section reference from TrafficRule
        rule = db.query(TrafficRule).filter(TrafficRule.category == v.category).first()
        section = rule.section_reference if rule else "Section 177"
        
        # Build textual penalties summary
        fine_text = ", ".join([f"{k.replace('_', ' ').title()}: \u20b9{val}" for k, val in base_fines.items() if val > 0])
        penalty_desc = f"Fines: {fine_text}." if fine_text else "Fine as per rules."
        
        court_only = v.violation_id in ["drunk_driving"]
        
        results.append({
            "id": v.violation_id,
            "name": v.violation_name,
            "section": section,
            "category": v.category,
            "description": v.description,
            "base_fines": base_fines,
            "repeat_fines": repeat_fines,
            "penalties": penalty_desc,
            "court_only": court_only
        })
    return results

@router.get("/compare/{violation_id}")
def compare_state_fines(violation_id: str, db: Session = Depends(get_db)):
    violation = db.query(Violation).filter(Violation.violation_id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Traffic violation not found")
        
    penalties = db.query(ViolationPenalty).filter(ViolationPenalty.violation_id == violation_id).all()
    
    comparison = {}
    
    state_names = {
        "delhi": "Delhi (NCT)",
        "karnataka": "Karnataka",
        "maharashtra": "Maharashtra",
        "tamil_nadu": "Tamil Nadu",
        "west_bengal": "West Bengal",
        "telangana": "Telangana"
    }
    
    for s_key, s_name in state_names.items():
        state_code_map = {
            "delhi": "DL",
            "karnataka": "KA",
            "maharashtra": "MH",
            "tamil_nadu": "TN",
            "west_bengal": "WB",
            "telangana": "TG"
        }
        target_code = state_code_map.get(s_key)
        state_model = db.query(State).filter(State.state_code.ilike(target_code)).first()
        
        state_id = state_model.state_id if state_model else None
        state_penalties = [p for p in penalties if p.state_id == state_id] if state_id else []
        
        rate = 0
        if state_penalties:
            lmv_penalty = next((p for p in state_penalties if p.vehicle_type_id in ["lmv", "car"]), None)
            tw_penalty = next((p for p in state_penalties if p.vehicle_type_id in ["two_wheeler", "2w"]), None)
            
            if lmv_penalty:
                rate = lmv_penalty.first_offense_fine or 0
            elif tw_penalty:
                rate = tw_penalty.first_offense_fine or 0
            else:
                rate = state_penalties[0].first_offense_fine or 0
                
        comparison[s_key] = {
            "state_name": s_name,
            "fine_rate": rate,
            "court_only": violation_id in ["drunk_driving"]
        }
        
    rule = db.query(TrafficRule).filter(TrafficRule.category == violation.category).first()
    section_ref = rule.section_reference if rule else "Section 177"
    
    return {
        "violation_id": violation_id,
        "name": violation.violation_name,
        "section": section_ref,
        "comparison": comparison
    }
