import os
import sys
# Add parent directory to path so we can import backend packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base, SessionLocal
from backend.models import TrafficRule, StateOverride, Vehicle, Challan, ChallanItem

# Central Motor Vehicles Act 2019 baseline rules
RULES_DATA = [
    {
        "id": "no_helmet",
        "section": "Section 129 / 194D",
        "name": "Riding without Helmet",
        "category": "Safety Equipment",
        "description": "Riding a two-wheeler without a protective headgear conforming to standards (BIS), or failure to secure it properly.",
        "base_fines": {"two_wheeler": 1000, "three_wheeler": 0, "lmv": 0, "hgv": 0, "other": 0},
        "repeat_fines": {"two_wheeler": 1000},
        "penalties": "Fine of ₹1,000 and disqualification/suspension of Driving License for a period of 3 months.",
        "court_only": False
    },
    {
        "id": "triple_riding",
        "section": "Section 128 / 194C",
        "name": "Triple Riding on Two-Wheeler",
        "category": "Safety Equipment",
        "description": "Riding a two-wheeler with more than one pillion rider (carrying more than two persons in total).",
        "base_fines": {"two_wheeler": 1000, "three_wheeler": 0, "lmv": 0, "hgv": 0, "other": 0},
        "repeat_fines": {"two_wheeler": 1000},
        "penalties": "Fine of ₹1,000 and disqualification of license for 3 months.",
        "court_only": False
    },
    {
        "id": "no_seatbelt",
        "section": "Section 194B(1)",
        "name": "Driving without Seatbelt",
        "category": "Safety Equipment",
        "description": "Operating a motor vehicle without wearing a safety seatbelt, or carrying passengers in the front seat who are not wearing a seatbelt.",
        "base_fines": {"two_wheeler": 0, "three_wheeler": 0, "lmv": 1000, "hgv": 1000, "other": 1000},
        "repeat_fines": {"lmv": 1000, "hgv": 1000, "other": 1000},
        "penalties": "Fine of ₹1,000.",
        "court_only": False
    },
    {
        "id": "drunk_driving",
        "section": "Section 185",
        "name": "Drunk Driving / Driving under Influence",
        "category": "Speeding & Driving",
        "description": "Driving a vehicle with Blood Alcohol Concentration (BAC) exceeding 30 mg per 100 ml of blood, or under the influence of drugs.",
        "base_fines": {"two_wheeler": 10000, "three_wheeler": 10000, "lmv": 10000, "hgv": 10000, "other": 10000},
        "repeat_fines": {"two_wheeler": 15000, "three_wheeler": 15000, "lmv": 15000, "hgv": 15000, "other": 15000},
        "penalties": "First Offense: Fine up to ₹10,000 and/or imprisonment up to 6 months. Subsequent Offense: Fine up to ₹15,000 and/or imprisonment up to 2 years.",
        "court_only": True
    },
    {
        "id": "speeding",
        "section": "Section 183(1)",
        "name": "Over-speeding",
        "category": "Speeding & Driving",
        "description": "Driving a motor vehicle in contravention of the speed limits set for that road/zone.",
        "base_fines": {"two_wheeler": 1000, "three_wheeler": 1000, "lmv": 1000, "hgv": 2000, "other": 1000},
        "repeat_fines": {"two_wheeler": 2000, "three_wheeler": 2000, "lmv": 2000, "hgv": 4000, "other": 2000},
        "penalties": "LMV fine of ₹1,000 - ₹2,000. Medium/Heavy vehicles fine of ₹2,000 - ₹4,000. Subsequent offense triggers impounding of driving license.",
        "court_only": False
    },
    {
        "id": "red_light_jumping",
        "section": "Section 184 (Dangerous Driving)",
        "name": "Jumping Traffic Red Light",
        "category": "Traffic Violation",
        "description": "Failing to stop at a red traffic signal, causing danger to other road users.",
        "base_fines": {"two_wheeler": 1000, "three_wheeler": 1000, "lmv": 1000, "hgv": 2000, "other": 1000},
        "repeat_fines": {"two_wheeler": 2000, "three_wheeler": 2000, "lmv": 2000, "hgv": 5000, "other": 2000},
        "penalties": "Fine of ₹1,000 to ₹5,000 and/or imprisonment for 6 months to 1 year, and license suspension.",
        "court_only": False
    },
    {
        "id": "using_mobile",
        "section": "Section 184(c)",
        "name": "Using Mobile Handheld Device while Driving",
        "category": "Speeding & Driving",
        "description": "Using a mobile phone or handheld communication device while operating a vehicle (except for navigation in a hands-free manner).",
        "base_fines": {"two_wheeler": 1000, "three_wheeler": 1000, "lmv": 5000, "hgv": 5000, "other": 5000},
        "repeat_fines": {"two_wheeler": 2000, "three_wheeler": 2000, "lmv": 10000, "hgv": 10000, "other": 10000},
        "penalties": "Fine of ₹1,000 to ₹5,000 for first-time offense. Subsequent offense up to ₹10,000.",
        "court_only": False
    },
    {
        "id": "no_driving_license",
        "section": "Section 181",
        "name": "Driving Without License",
        "category": "Documents",
        "description": "Driving a motor vehicle on public roads without holding a valid, active driving license for that specific class of vehicle.",
        "base_fines": {"two_wheeler": 5000, "three_wheeler": 5000, "lmv": 5000, "hgv": 5000, "other": 5000},
        "repeat_fines": {"two_wheeler": 5000, "three_wheeler": 5000, "lmv": 5000, "hgv": 5000, "other": 5000},
        "penalties": "Fine of ₹5,000 and/or imprisonment up to 3 months.",
        "court_only": False
    },
    {
        "id": "no_rc",
        "section": "Section 192",
        "name": "Driving Unregistered Vehicle (No RC)",
        "category": "Documents",
        "description": "Driving or using a motor vehicle without a valid registration certificate (RC).",
        "base_fines": {"two_wheeler": 5000, "three_wheeler": 5000, "lmv": 5000, "hgv": 5000, "other": 5000},
        "repeat_fines": {"two_wheeler": 10000, "three_wheeler": 10000, "lmv": 10000, "hgv": 10000, "other": 10000},
        "penalties": "First offense: Fine up to ₹5,000. Subsequent offense: Fine up to ₹10,000 or imprisonment up to 1 year.",
        "court_only": False
    },
    {
        "id": "no_insurance",
        "section": "Section 196",
        "name": "Driving Without Insurance Cover",
        "category": "Documents",
        "description": "Operating a motor vehicle without a valid third-party insurance cover.",
        "base_fines": {"two_wheeler": 2000, "three_wheeler": 2000, "lmv": 2000, "hgv": 4000, "other": 2000},
        "repeat_fines": {"two_wheeler": 4000, "three_wheeler": 4000, "lmv": 4000, "hgv": 4000, "other": 4000},
        "penalties": "First offense: Fine of ₹2,000 and/or imprisonment up to 3 months. Subsequent offense: Fine of ₹4,000 and/or imprisonment up to 3 months.",
        "court_only": False
    },
    {
        "id": "no_pucc",
        "section": "Section 190(2)",
        "name": "Driving Without PUC Certificate",
        "category": "Documents",
        "description": "Driving a vehicle violating safety and air pollution standards (not possessing a valid Pollution Under Control certificate).",
        "base_fines": {"two_wheeler": 10000, "three_wheeler": 10000, "lmv": 10000, "hgv": 10000, "other": 10000},
        "repeat_fines": {"two_wheeler": 10000, "three_wheeler": 10000, "lmv": 10000, "hgv": 10000, "other": 10000},
        "penalties": "Fine of ₹10,000, up to 3 months imprisonment, and Driving License disqualification for 3 months.",
        "court_only": False
    },
    {
        "id": "obstructive_parking",
        "section": "Section 122 / 177",
        "name": "Wrong / Obstructive Parking",
        "category": "Parking",
        "description": "Parking a vehicle in a public place in a manner that causes or is likely to cause danger, obstruction, or undue inconvenience to other users.",
        "base_fines": {"two_wheeler": 500, "three_wheeler": 500, "lmv": 500, "hgv": 1000, "other": 500},
        "repeat_fines": {"two_wheeler": 1500, "three_wheeler": 1500, "lmv": 1500, "hgv": 1500, "other": 1500},
        "penalties": "Fine of ₹500 for first offense, ₹1,500 for subsequent. Towing fees apply additionally depending on city.",
        "court_only": False
    },
    {
        "id": "emergency_vehicle_blocking",
        "section": "Section 194E",
        "name": "Blocking Emergency Vehicles",
        "category": "Traffic Violation",
        "description": "Failing to draw to the side of the road to allow free passage to fire service vehicles, ambulances, or other emergency vehicles.",
        "base_fines": {"two_wheeler": 10000, "three_wheeler": 10000, "lmv": 10000, "hgv": 10000, "other": 10000},
        "repeat_fines": {"two_wheeler": 10000, "three_wheeler": 10000, "lmv": 10000, "hgv": 10000, "other": 10000},
        "penalties": "Fine of ₹10,000 and/or imprisonment up to 6 months.",
        "court_only": False
    },
    {
        "id": "no_entry",
        "section": "Section 115 / 194C / 177",
        "name": "Driving in No-Entry Zone / Against Traffic",
        "category": "Traffic Violation",
        "description": "Driving a vehicle into a designated 'No-Entry' zone or in a direction opposite to the flow of traffic (one-way violation).",
        "base_fines": {"two_wheeler": 1000, "three_wheeler": 1000, "lmv": 2000, "hgv": 5000, "other": 2000},
        "repeat_fines": {"two_wheeler": 2000, "three_wheeler": 2000, "lmv": 4000, "hgv": 10000, "other": 4000},
        "penalties": "Compounding fine varies by state; baseline begins at ₹500-₹2,000 depending on vehicle size.",
        "court_only": False
    }
]

# State-specific overrides
STATE_OVERRIDES_DATA = {
    "delhi": {
        "no_helmet": {"two_wheeler": 1000},
        "triple_riding": {"two_wheeler": 1000},
        "no_seatbelt": {"lmv": 1000},
        "speeding": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "red_light_jumping": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "using_mobile": {"two_wheeler": 1000, "lmv": 5000, "hgv": 5000},
        "no_driving_license": {"all": 5000},
        "no_rc": {"all": 5000},
        "no_insurance": {"two_wheeler": 2000, "lmv": 2000, "hgv": 4000},
        "no_pucc": {"all": 10000},
        "obstructive_parking": {"two_wheeler": 500, "lmv": 500, "hgv": 1000},
        "no_entry": {"two_wheeler": 1000, "lmv": 2000, "hgv": 5000}
    },
    "karnataka": {
        "no_helmet": {"two_wheeler": 500},
        "triple_riding": {"two_wheeler": 500},
        "no_seatbelt": {"lmv": 500},
        "speeding": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "red_light_jumping": {"two_wheeler": 500, "lmv": 1000, "hgv": 2000},
        "using_mobile": {"two_wheeler": 1500, "lmv": 5000, "hgv": 5000},
        "no_driving_license": {"all": 5000},
        "no_rc": {"all": 5000},
        "no_insurance": {"two_wheeler": 1000, "lmv": 2000, "hgv": 4000},
        "no_pucc": {"all": 10000},
        "obstructive_parking": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "no_entry": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000}
    },
    "maharashtra": {
        "no_helmet": {"two_wheeler": 500},
        "triple_riding": {"two_wheeler": 1000},
        "no_seatbelt": {"lmv": 500},
        "speeding": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "red_light_jumping": {"two_wheeler": 500, "lmv": 1000, "hgv": 2000},
        "using_mobile": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "no_driving_license": {"all": 5000},
        "no_rc": {"all": 5000},
        "no_insurance": {"two_wheeler": 2000, "lmv": 2000, "hgv": 4000},
        "no_pucc": {"all": 10000},
        "obstructive_parking": {"two_wheeler": 500, "lmv": 500, "hgv": 1000},
        "no_entry": {"two_wheeler": 1000, "lmv": 2000, "hgv": 5000}
    },
    "tamil_nadu": {
        "no_helmet": {"two_wheeler": 1000},
        "triple_riding": {"two_wheeler": 1000},
        "no_seatbelt": {"lmv": 1000},
        "speeding": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "red_light_jumping": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "using_mobile": {"two_wheeler": 1000, "lmv": 5000, "hgv": 5000},
        "no_driving_license": {"all": 5000},
        "no_rc": {"all": 5000},
        "no_insurance": {"two_wheeler": 2000, "lmv": 2000, "hgv": 4000},
        "no_pucc": {"all": 10000},
        "obstructive_parking": {"two_wheeler": 500, "lmv": 500, "hgv": 1000},
        "no_entry": {"two_wheeler": 1000, "lmv": 2000, "hgv": 5000}
    },
    "west_bengal": {
        "no_helmet": {"two_wheeler": 1000},
        "triple_riding": {"two_wheeler": 1000},
        "no_seatbelt": {"lmv": 1000},
        "speeding": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "red_light_jumping": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "using_mobile": {"two_wheeler": 2000, "lmv": 2000, "hgv": 5000},
        "no_driving_license": {"all": 5000},
        "no_rc": {"all": 5000},
        "no_insurance": {"two_wheeler": 2000, "lmv": 2000, "hgv": 4000},
        "no_pucc": {"all": 10000},
        "obstructive_parking": {"two_wheeler": 500, "lmv": 500, "hgv": 1000},
        "no_entry": {"two_wheeler": 2000, "lmv": 2000, "hgv": 5000}
    },
    "telangana": {
        "no_helmet": {"two_wheeler": 200},
        "triple_riding": {"two_wheeler": 1000},
        "no_seatbelt": {"lmv": 250},
        "speeding": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "red_light_jumping": {"two_wheeler": 1000, "lmv": 1000, "hgv": 2000},
        "using_mobile": {"two_wheeler": 1000, "lmv": 2000, "hgv": 5000},
        "no_driving_license": {"all": 5000},
        "no_rc": {"all": 5000},
        "no_insurance": {"two_wheeler": 2000, "lmv": 2000, "hgv": 4000},
        "no_pucc": {"all": 10000},
        "obstructive_parking": {"two_wheeler": 200, "lmv": 200, "hgv": 500},
        "no_entry": {"two_wheeler": 200, "lmv": 1000, "hgv": 2000}
    }
}

# Sample vehicles & their active/closed challans
VEHICLES_DATA = [
    {
        "vehicle_number": "DL3CA1234",
        "vehicle_type": "lmv",
        "owner_name": "Rahul Sharma",
        "registration_date": "2021-08-15"
    },
    {
        "vehicle_number": "KA03MM5678",
        "vehicle_type": "two_wheeler",
        "owner_name": "Priya Nair",
        "registration_date": "2023-04-10"
    },
    {
        "vehicle_number": "MH12AB9012",
        "vehicle_type": "two_wheeler",
        "owner_name": "Amit Patel",
        "registration_date": "2022-11-20"
    }
]

CHALLANS_DATA = [
    {
        "challan_number": "DL00010928",
        "vehicle_number": "DL3CA1234",
        "state_code": "delhi",
        "violation_date": "2026-05-20 11:30",
        "total_amount": 1000,
        "status": "Paid",
        "items": [
            {
                "violation_id": "speeding",
                "section": "Section 183(1)",
                "description": "Over-speeding LMV (Car) on DND Flyover",
                "fine_amount": 1000
            }
        ]
    },
    {
        "challan_number": "DL00029304",
        "vehicle_number": "DL3CA1234",
        "state_code": "delhi",
        "violation_date": "2026-05-25 15:45",
        "total_amount": 1000,
        "status": "Unpaid",
        "items": [
            {
                "violation_id": "no_seatbelt",
                "section": "Section 194B(1)",
                "description": "Driver not wearing safety seatbelt",
                "fine_amount": 1000
            }
        ]
    },
    {
        "challan_number": "KA0091827",
        "vehicle_number": "KA03MM5678",
        "state_code": "karnataka",
        "violation_date": "2026-05-22 09:15",
        "total_amount": 500,
        "status": "Unpaid",
        "items": [
            {
                "violation_id": "no_helmet",
                "section": "Section 129 / 194D",
                "description": "Riding without headgear protective helmet",
                "fine_amount": 500
            }
        ]
    },
    {
        "challan_number": "KA0093849",
        "vehicle_number": "KA03MM5678",
        "state_code": "karnataka",
        "violation_date": "2026-05-28 22:10",
        "total_amount": 10000,
        "status": "In Court",
        "items": [
            {
                "violation_id": "drunk_driving",
                "section": "Section 185",
                "description": "Drunk driving two-wheeler (BAC > 30mg)",
                "fine_amount": 10000
            }
        ]
    },
    {
        "challan_number": "MH0082736",
        "vehicle_number": "MH12AB9012",
        "state_code": "maharashtra",
        "violation_date": "2026-05-27 18:20",
        "total_amount": 1000,
        "status": "Unpaid",
        "items": [
            {
                "violation_id": "triple_riding",
                "section": "Section 128 / 194C",
                "description": "Triple riding on motorcycle in Pune",
                "fine_amount": 1000
            }
        ]
    }
]

def seed_database():
    print("Initializing Database and Seeding Data...")
    
    # Drop and recreate all tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. Insert Traffic Rules
        for r_data in RULES_DATA:
            rule = TrafficRule(
                id=r_data["id"],
                section=r_data["section"],
                name=r_data["name"],
                category=r_data["category"],
                description=r_data["description"],
                base_fines=r_data["base_fines"],
                repeat_fines=r_data["repeat_fines"],
                penalties=r_data["penalties"],
                court_only=r_data["court_only"]
            )
            db.add(rule)
        db.commit()
        print(f"Seeded {len(RULES_DATA)} traffic rules.")

        # 2. Insert State Overrides
        override_count = 0
        for state_code, overrides in STATE_OVERRIDES_DATA.items():
            for violation_id, fine_amt in overrides.items():
                override = StateOverride(
                    state_code=state_code,
                    violation_id=violation_id,
                    fine_amount=fine_amt
                )
                db.add(override)
                override_count += 1
        db.commit()
        print(f"Seeded {override_count} state compounding overrides.")

        # 3. Insert Vehicles
        for v_data in VEHICLES_DATA:
            vehicle = Vehicle(
                vehicle_number=v_data["vehicle_number"],
                vehicle_type=v_data["vehicle_type"],
                owner_name=v_data["owner_name"],
                registration_date=v_data["registration_date"]
            )
            db.add(vehicle)
        db.commit()
        print(f"Seeded {len(VEHICLES_DATA)} vehicles.")

        # 4. Insert Challans and Challan Items
        for c_data in CHALLANS_DATA:
            challan = Challan(
                challan_number=c_data["challan_number"],
                vehicle_number=c_data["vehicle_number"],
                state_code=c_data["state_code"],
                violation_date=c_data["violation_date"],
                total_amount=c_data["total_amount"],
                status=c_data["status"]
            )
            db.add(challan)
            db.flush() # Flushes to get challan.id
            
            for item_data in c_data["items"]:
                c_item = ChallanItem(
                    challan_id=challan.id,
                    violation_id=item_data["violation_id"],
                    section=item_data["section"],
                    description=item_data["description"],
                    fine_amount=item_data["fine_amount"]
                )
                db.add(c_item)
        db.commit()
        print(f"Seeded {len(CHALLANS_DATA)} challans and items.")

        print("Seeding completed successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
