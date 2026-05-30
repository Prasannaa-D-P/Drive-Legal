import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models import Vehicle, Challan, ChallanItem, TrafficRule

def sanitize_vehicle_number(vn: str) -> str:
    return vn.upper().replace(" ", "").replace("-", "")

def get_state_code_from_vehicle(vn: str) -> str:
    # Extract first two characters, e.g. "DL", "KA", "MH"
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
    return mapping.get(prefix, "delhi") # Default to delhi if unknown prefix

def fetch_rto_challans(vehicle_number: str, db: Session):
    clean_vn = sanitize_vehicle_number(vehicle_number)
    
    # 1. Fetch or create vehicle details in our DB
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_number == clean_vn).first()
    if not vehicle:
        # Determine vehicle type (let's assume two-wheeler if search contains 'B' or 'M', else LMV/car)
        v_type = "two_wheeler" if any(x in clean_vn for x in ["B", "M", "S"]) else "lmv"
        
        # Register new vehicle
        vehicle = Vehicle(
            vehicle_number=clean_vn,
            vehicle_type=v_type,
            owner_name=f"Mock Owner ({clean_vn})",
            registration_date=(datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        print(f"[RTO Service] Registered new vehicle profile: {clean_vn}")

    # 2. Fetch existing challans from database
    challans = db.query(Challan).filter(Challan.vehicle_number == clean_vn).all()
    
    # 3. If no challans exist, auto-generate a mock pending challan to simulate a real government portal response
    if not challans:
        state_key = get_state_code_from_vehicle(clean_vn)
        
        # Define mock violation cases
        mock_violations = {
            "delhi": {"id": "speeding", "desc": "Over-speeding caught on speed camera at DND Flyway"},
            "karnataka": {"id": "no_helmet", "desc": "Riding two-wheeler without helmet on MG Road"},
            "maharashtra": {"id": "no_seatbelt", "desc": "Driving car without seatbelt on Bandra-Worli Sea Link"},
            "tamil_nadu": {"id": "using_mobile", "desc": "Using handheld mobile phone while driving on Anna Salai"},
            "west_bengal": {"id": "no_pucc", "desc": "Failed to display valid PUC certificate during checking"},
            "telangana": {"id": "red_light_jumping", "desc": "Jumping red traffic light signal at Gachibowli Junction"}
        }
        
        v_case = mock_violations.get(state_key, {"id": "speeding", "desc": "Over-speeding violation"})
        rule = db.query(TrafficRule).filter(TrafficRule.id == v_case["id"]).first()
        
        if rule:
            # Determine fine amount (use base or state override)
            fine = rule.base_fines.get(vehicle.vehicle_type, 1000)
            
            # Create Challan
            random_digits = "".join([str(random.randint(0, 9)) for _ in range(8)])
            challan_no = f"{state_key[:2].upper()}{random_digits}"
            
            new_challan = Challan(
                challan_number=challan_no,
                vehicle_number=clean_vn,
                state_code=state_key,
                violation_date=(datetime.now() - timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d %H:%M"),
                total_amount=fine,
                status="Unpaid"
            )
            db.add(new_challan)
            db.flush() # Get new_challan.id
            
            # Create Challan Item
            new_item = ChallanItem(
                challan_id=new_challan.id,
                violation_id=rule.id,
                section=rule.section,
                description=v_case["desc"],
                fine_amount=fine
            )
            db.add(new_item)
            db.commit()
            
            # Query again to return structured object
            challans = [new_challan]
            print(f"[RTO Service] Generated mock RTO challan {challan_no} for vehicle {clean_vn}")

    return {
        "vehicle": vehicle,
        "challans": challans
    }
