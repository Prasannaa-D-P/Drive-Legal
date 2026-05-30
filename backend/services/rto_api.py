import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models import Challan, State, ViolationPenalty, Violation, TrafficRule

def sanitize_vehicle_number(vn: str) -> str:
    return vn.upper().replace(" ", "").replace("-", "")

def get_state_code_from_vehicle(vn: str) -> str:
    prefix = vn[:2]
    mapping = {
        "DL": "delhi",
        "KA": "karnataka",
        "MH": "maharashtra",
        "TN": "tamil_nadu",
        "WB": "west_bengal",
        "TG": "telangana",
        "TS": "telangana"
    }
    return mapping.get(prefix, "delhi")

def fetch_rto_challans(vehicle_number: str, db: Session):
    clean_vn = sanitize_vehicle_number(vehicle_number)
    
    # 1. Transient mock vehicle details
    vehicle = {
        "vehicle_number": clean_vn,
        "vehicle_type": "two_wheeler" if any(x in clean_vn for x in ["B", "M", "S"]) else "lmv",
        "owner_name": f"Mock Owner ({clean_vn})",
        "registration_date": (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    }

    # 2. Fetch existing challans from database
    challans = db.query(Challan).filter(Challan.vehicle_number == clean_vn).all()
    
    # 3. If no challans exist, auto-generate a mock pending challan to simulate a real government portal response
    if not challans:
        state_key = get_state_code_from_vehicle(clean_vn)
        
        mock_violations = {
            "delhi": {"id": "speeding", "desc": "Over-speeding caught on speed camera at DND Flyway"},
            "karnataka": {"id": "no_helmet", "desc": "Riding two-wheeler without helmet on MG Road"},
            "maharashtra": {"id": "no_seatbelt", "desc": "Driving car without seatbelt on Bandra-Worli Sea Link"},
            "tamil_nadu": {"id": "using_mobile", "desc": "Using handheld mobile phone while driving on Anna Salai"},
            "west_bengal": {"id": "no_pucc", "desc": "Failed to display valid PUC certificate during checking"},
            "telangana": {"id": "red_light_jumping", "desc": "Jumping red traffic light signal at Gachibowli Junction"}
        }
        
        v_case = mock_violations.get(state_key, {"id": "speeding", "desc": "Over-speeding violation"})
        
        # Resolve state and violation details from the 11-table schema
        state_code_map = {
            "delhi": "DL",
            "karnataka": "KA",
            "maharashtra": "MH",
            "tamil_nadu": "TN",
            "west_bengal": "WB",
            "telangana": "TG"
        }
        target_code = state_code_map.get(state_key, "DL")
        state_model = db.query(State).filter(State.state_code.ilike(target_code)).first()
        state_id = state_model.state_id if state_model else "state_dl"
        
        v_type_id = "2w" if vehicle["vehicle_type"] == "two_wheeler" else "car"
        
        penalty = db.query(ViolationPenalty).filter(
            ViolationPenalty.violation_id == v_case["id"],
            ViolationPenalty.vehicle_type_id == v_type_id,
            ViolationPenalty.state_id == state_id
        ).first()
        
        fine = penalty.first_offense_fine if penalty else 1000
        
        issued_time = int((datetime.now() - timedelta(days=random.randint(1, 10))).timestamp() * 1000)
        deadline_time = issued_time + (60 * 24 * 3600 * 1000) # 60 days
        
        # Get violation details
        violation = db.query(Violation).filter(Violation.violation_id == v_case["id"]).first()
        v_name = violation.violation_name if violation else "Traffic Violation"
        
        # Find category rules
        rule = db.query(TrafficRule).filter(TrafficRule.category == (violation.category if violation else "Safety")).first()
        section_ref = rule.section_reference if rule else "Section 177"
        
        new_challan = Challan(
            id=str(uuid.uuid4()),
            challan_number=f"{state_key[:2].upper()}{''.join([str(random.randint(0, 9)) for _ in range(8)])}",
            vehicle_number=clean_vn,
            violation_name=v_name,
            location=f"{state_key.title()} Highway Guard",
            amount=fine,
            status="Unpaid",
            issued_at=issued_time,
            deadline_at=deadline_time,
            section=section_ref,
            act="Motor Vehicles Act 2019",
            consequences=f"Fine of \u20b9{fine} compoundable under Motor Vehicle rules."
        )
        db.add(new_challan)
        db.commit()
        db.refresh(new_challan)
        
        challans = [new_challan]
        print(f"[RTO Service] Generated mock RTO challan {new_challan.challan_number} for vehicle {clean_vn}")

    return {
        "vehicle": vehicle,
        "challans": challans
    }
