from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.database import get_db
from backend.models import TrafficRule, StateOverride
from backend.schemas import TrafficRuleBase, StateOverrideBase

router = APIRouter(
    prefix="/rules",
    tags=["Traffic Rules"]
)

@router.get("/", response_model=List[TrafficRuleBase])
def read_all_rules(db: Session = Depends(get_db)):
    rules = db.query(TrafficRule).all()
    return rules

@router.get("/compare/{violation_id}")
def compare_state_fines(violation_id: str, db: Session = Depends(get_db)):
    rule = db.query(TrafficRule).filter(TrafficRule.id == violation_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Traffic violation not found")
        
    overrides = db.query(StateOverride).filter(StateOverride.violation_id == violation_id).all()
    
    comparison = {}
    
    # State names mapping
    state_names = {
        "delhi": "Delhi (NCT)",
        "karnataka": "Karnataka",
        "maharashtra": "Maharashtra",
        "tamil_nadu": "Tamil Nadu",
        "west_bengal": "West Bengal",
        "telangana": "Telangana"
    }
    
    for s_key, s_name in state_names.items():
        # Find if override exists
        match = next((ov for ov in overrides if ov.state_code == s_key), None)
        
        # Calculate standard representation fine (usually LMV or two-wheeler)
        base_amt = rule.base_fines.get("lmv") or rule.base_fines.get("two_wheeler") or rule.base_fines.get("other") or 0
        
        if match:
            override_amt = match.fine_amount.get("all") or match.fine_amount.get("lmv") or match.fine_amount.get("two_wheeler") or base_amt
            rate = override_amt
        else:
            rate = base_amt
            
        comparison[s_key] = {
            "state_name": s_name,
            "fine_rate": rate,
            "court_only": rule.court_only
        }
        
    return {
        "violation_id": violation_id,
        "name": rule.name,
        "section": rule.section,
        "comparison": comparison
    }

@router.get("/overrides", response_model=List[StateOverrideBase])
def read_all_overrides(db: Session = Depends(get_db)):
    overrides = db.query(StateOverride).all()
    return overrides
