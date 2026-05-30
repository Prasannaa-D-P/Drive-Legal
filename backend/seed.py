import os
import sys
import uuid
import random
import time
from datetime import datetime, timedelta
import pypdf

# Add parent directory to path so we can import backend packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base, SessionLocal
from backend.models import (
    Country, State, City, TrafficRule, VehicleType, Violation, 
    ViolationPenalty, ChallanCalculation, FAQKnowledge, SyncVersion, 
    LegalSource, Challan
)

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
        "penalties": "Fine of \u20b91,000 and disqualification/suspension of Driving License for a period of 3 months.",
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
        "penalties": "Fine of \u20b91,000 and disqualification of license for 3 months.",
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
        "penalties": "Fine of \u20b91,000.",
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
        "penalties": "First Offense: Fine up to \u20b910,000 and/or imprisonment up to 6 months. Subsequent Offense: Fine up to \u20b915,000 and/or imprisonment up to 2 years.",
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
        "penalties": "LMV fine of \u20b91,000 - \u20b92,000. Medium/Heavy vehicles fine of \u20b92,000 - \u20b94,000. Subsequent offense triggers impounding of driving license.",
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
        "penalties": "Fine of \u20b91,000 to \u20b95,000 and/or imprisonment for 6 months to 1 year, and license suspension.",
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
        "penalties": "Fine of \u20b91,000 to \u20b95,000 for first-time offense. Subsequent offense up to \u20b910,000.",
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
        "penalties": "Fine of \u20b95,000 and/or imprisonment up to 3 months.",
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
        "penalties": "First offense: Fine up to \u20b95,000. Subsequent offense: Fine up to \u20b910,000 or imprisonment up to 1 year.",
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
        "penalties": "First offense: Fine of \u20b92,000 and/or imprisonment up to 3 months. Subsequent offense: Fine of \u20b94,000 and/or imprisonment up to 3 months.",
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
        "penalties": "Fine of \u20b910,000, up to 3 months imprisonment, and Driving License disqualification for 3 months.",
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
        "penalties": "Fine of \u20b9500 for first offense, \u20b91,500 for subsequent. Towing fees apply additionally depending on city.",
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
        "penalties": "Fine of \u20b910,000 and/or imprisonment up to 6 months.",
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
        "penalties": "Compounding fine varies by state; baseline begins at \u20b9500-\u20b92,000 depending on vehicle size.",
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

# Compatibility challans data
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

def gen_uuid(name: str) -> str:
    # Deterministic UUID generation
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, name))

def create_database_if_not_exists():
    from backend.database import DATABASE_URL
    if not DATABASE_URL.startswith("postgresql"):
        return
        
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    import urllib.parse as urlparse
    
    url = urlparse.urlparse(DATABASE_URL)
    username = url.username
    password = url.password
    host = url.hostname
    port = url.port or 5432
    dbname = url.path[1:]
    
    print(f"Connecting to database server on {host}:{port} as user '{username}' to verify database '{dbname}'...")
    try:
        conn = psycopg2.connect(
            user=username,
            password=password,
            host=host,
            port=port,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Database '{dbname}' does not exist. Creating...")
            cursor.execute(f"CREATE DATABASE {dbname}")
            print(f"Database '{dbname}' created successfully.")
        else:
            print(f"Database '{dbname}' already exists.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Warning: Failed to verify/create database on server: {e}")

def extract_pdf_data(db):
    print("Reading and parsing official laws PDFs using pypdf...")
    
    # 1. India_Traffic_Rules_and_Acts_Guide.pdf
    guide_path = "law data/India_Traffic_Rules_and_Acts_Guide.pdf"
    if os.path.exists(guide_path):
        try:
            reader = pypdf.PdfReader(guide_path)
            num_pages = len(reader.pages)
            meta = reader.metadata
            title = meta.title if meta and meta.title else "India Traffic Rules and Acts Guide"
            
            source_id = gen_uuid("source_guide")
            guide_source = LegalSource(
                source_id=source_id,
                country_id=gen_uuid("country_IN"),
                state_id=gen_uuid("state_DL"),
                source_name="India Traffic Rules and Acts Guide",
                source_url="https://morth.nic.in/",
                document_title=title,
                publication_date="2026",
                last_verified=datetime.utcnow()
            )
            db.add(guide_source)
            
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
                
            # Parse state highlights to insert as FAQKnowledge
            lines = full_text.split("\n")
            for line in lines:
                if ":" in line and any(state in line.lower() for state in ["tamil nadu", "karnataka", "maharashtra", "delhi", "telangana", "west bengal"]):
                    parts = line.split(":", 1)
                    state_name = parts[0].replace("-", "").strip()
                    highlight_text = parts[1].strip()
                    
                    state_key_map = {
                        "delhi": "state_DL",
                        "karnataka": "state_KA",
                        "maharashtra": "state_MH",
                        "tamil nadu": "state_TN",
                        "west bengal": "state_WB",
                        "telangana": "state_TG"
                    }
                    state_id = gen_uuid(state_key_map.get(state_name.lower(), "state_DL"))
                    
                    faq_id = gen_uuid(f"faq_highlight_{state_name}")
                    faq = FAQKnowledge(
                        faq_id=faq_id,
                        country_id=gen_uuid("country_IN"),
                        state_id=state_id,
                        question=f"What are the main traffic enforcement highlights in {state_name}?",
                        answer=highlight_text,
                        category="Regional Highlights",
                        last_updated=datetime.utcnow()
                    )
                    db.add(faq)
            print("Extracted highlights and added FAQs from India_Traffic_Rules_and_Acts_Guide.pdf.")
        except Exception as e:
            print(f"Error parsing guide PDF: {e}")

    # 2. Motor Vehicles (Amendment) Act, 2019.pdf
    mva_path = "law data/Motor Vehicles (Amendment) Act, 2019.pdf"
    if os.path.exists(mva_path):
        try:
            reader = pypdf.PdfReader(mva_path)
            num_pages = len(reader.pages)
            source_id = gen_uuid("source_mva2019")
            mva_source = LegalSource(
                source_id=source_id,
                country_id=gen_uuid("country_IN"),
                state_id=gen_uuid("state_DL"),
                source_name="Motor Vehicles (Amendment) Act, 2019",
                source_url="https://egazette.nic.in/",
                document_title="The Motor Vehicles (Amendment) Act, 2019 (No. 32 of 2019)",
                publication_date="2019",
                last_verified=datetime.utcnow()
            )
            db.add(mva_source)
            print(f"Parsed metadata for Motor Vehicles (Amendment) Act, 2019.pdf ({num_pages} pages).")
        except Exception as e:
            print(f"Error parsing MVA 2019 PDF: {e}")

    # 3. a1988-59.pdf
    act_path = "law data/a1988-59.pdf"
    if os.path.exists(act_path):
        try:
            reader = pypdf.PdfReader(act_path)
            num_pages = len(reader.pages)
            source_id = gen_uuid("source_mva1988")
            act_source = LegalSource(
                source_id=source_id,
                country_id=gen_uuid("country_IN"),
                state_id=gen_uuid("state_DL"),
                source_name="Motor Vehicles Act, 1988",
                source_url="https://legislative.gov.in/",
                document_title="The Motor Vehicles Act, 1988 (Act No. 59 of 1988)",
                publication_date="1988",
                last_verified=datetime.utcnow()
            )
            db.add(act_source)
            print(f"Parsed metadata for Motor Vehicles Act, 1988.pdf ({num_pages} pages).")
        except Exception as e:
            print(f"Error parsing MVA 1988 PDF: {e}")

def seed_database():
    create_database_if_not_exists()
    from sqlalchemy import text
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            print("Dropping existing tables with CASCADE...")
            connection.execute(text("DROP TABLE IF EXISTS challan_items, challans, traffic_rules, state_overrides, vehicles, profile, notifications, sync_queue, chat_sessions, chat_messages, countries, states, cities, vehicle_types, violations, violation_penalties, challan_calculations, faq_knowledge, sync_versions, legal_sources CASCADE"))
            transaction.commit()
        except Exception as err:
            transaction.rollback()
            print(f"Warning: Raw drop tables failed: {err}")
            
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Countries
        countries = [
            Country(country_id=gen_uuid("country_IN"), country_code="IN", country_name="India"),
            Country(country_id=gen_uuid("country_US"), country_code="US", country_name="United States"),
            Country(country_id=gen_uuid("country_UK"), country_code="UK", country_name="United Kingdom")
        ]
        db.add_all(countries)
        db.commit()
        print("Seeded countries.")

        # 2. States / Regions (India focus)
        state_data = {
            "DL": "Delhi (NCT)",
            "KA": "Karnataka",
            "MH": "Maharashtra",
            "TN": "Tamil Nadu",
            "WB": "West Bengal",
            "TG": "Telangana"
        }
        states = []
        for code, name in state_data.items():
            states.append(State(
                state_id=gen_uuid(f"state_{code}"),
                country_id=gen_uuid("country_IN"),
                state_code=code,
                state_name=name
            ))
        db.add_all(states)
        db.commit()
        print("Seeded states.")

        # 3. Cities
        city_data = [
            {"name": "New Delhi", "state_code": "DL", "lat": 28.6139, "lng": 77.2090},
            {"name": "Bengaluru", "state_code": "KA", "lat": 12.9716, "lng": 77.5946},
            {"name": "Mumbai", "state_code": "MH", "lat": 19.0760, "lng": 72.8777},
            {"name": "Chennai", "state_code": "TN", "lat": 13.0827, "lng": 80.2707},
            {"name": "Kolkata", "state_code": "WB", "lat": 22.5726, "lng": 88.3639},
            {"name": "Hyderabad", "state_code": "TG", "lat": 17.3850, "lng": 78.4867}
        ]
        cities = []
        for c in city_data:
            cities.append(City(
                city_id=gen_uuid(f"city_{c['name']}"),
                state_id=gen_uuid(f"state_{c['state_code']}"),
                city_name=c["name"],
                latitude=c["lat"],
                longitude=c["lng"]
            ))
        db.add_all(cities)
        db.commit()
        print("Seeded cities.")

        # 4. Vehicle Types
        v_types = [
            VehicleType(vehicle_type_id="2w", vehicle_name="Two-Wheeler", description="Motorcycle/Scooter/Moped"),
            VehicleType(vehicle_type_id="3w", vehicle_name="Three-Wheeler", description="Auto-rickshaw/E-rickshaw"),
            VehicleType(vehicle_type_id="car", vehicle_name="Light Motor Vehicle (LMV)", description="Passenger Car/SUV/Jeep"),
            VehicleType(vehicle_type_id="bus", vehicle_name="Medium/Heavy Passenger Vehicle", description="School Bus/Transit Bus"),
            VehicleType(vehicle_type_id="truck", vehicle_name="Heavy Goods Vehicle (HGV)", description="Freight Truck/Container/Dumper"),
            VehicleType(vehicle_type_id="other", vehicle_name="Other / Unspecified", description="Special purpose/Tractor/Construction")
        ]
        db.add_all(v_types)
        db.commit()
        print("Seeded vehicle types.")

        # 5. Violations
        violations = []
        for rule in RULES_DATA:
            violations.append(Violation(
                violation_id=rule["id"],
                violation_name=rule["name"],
                category=rule["category"],
                description=rule["description"]
            ))
        db.add_all(violations)
        db.commit()
        print("Seeded violations.")

        # 6. Violation Penalties (relational table)
        penalties_seeded = 0
        state_slugs = {
            "delhi": "DL",
            "karnataka": "KA",
            "maharashtra": "MH",
            "tamil_nadu": "TN",
            "west_bengal": "WB",
            "telangana": "TG"
        }
        
        # Mapping vehicle names to vtype IDs
        vtype_mapping = {
            "two_wheeler": "2w",
            "three_wheeler": "3w",
            "lmv": "car",
            "hgv": "truck",
            "other": "other"
        }

        # Loop over states
        for slug, state_code in state_slugs.items():
            state_id = gen_uuid(f"state_{state_code}")
            
            # Loop over violations
            for rule in RULES_DATA:
                v_id = rule["id"]
                
                # Check if state has specific overrides
                overrides = STATE_OVERRIDES_DATA.get(slug, {}).get(v_id, None)
                
                # Loop over vehicle types
                for name_slug, v_type_id in vtype_mapping.items():
                    # Base fine
                    base_fine = rule["base_fines"].get(name_slug, 0)
                    repeat_fine = rule["repeat_fines"].get(name_slug, base_fine * 2)
                    
                    if overrides:
                        # Override applies to 'all' or specific vehicle type
                        if "all" in overrides:
                            base_fine = overrides["all"]
                            repeat_fine = base_fine * 2
                        elif name_slug in overrides:
                            base_fine = overrides[name_slug]
                            repeat_fine = base_fine * 2
                            
                    # Drunk driving custom overrides
                    imprisonment = None
                    license_points = 0
                    seizure = False
                    
                    if v_id == "drunk_driving":
                        imprisonment = "Up to 6 months (1st) / 2 years (repeat)"
                        license_points = 4
                        seizure = True
                    elif v_id == "no_driving_license":
                        imprisonment = "Up to 3 months"
                        seizure = True
                    elif v_id == "no_rc":
                        seizure = True
                    elif v_id == "no_pucc":
                        imprisonment = "Up to 3 months"
                        license_points = 2
                    elif v_id == "no_helmet":
                        license_points = 1
                        
                    penalty = ViolationPenalty(
                        penalty_id=gen_uuid(f"penalty_{state_code}_{v_id}_{v_type_id}"),
                        violation_id=v_id,
                        vehicle_type_id=v_type_id,
                        country_id=gen_uuid("country_IN"),
                        state_id=state_id,
                        first_offense_fine=base_fine,
                        second_offense_fine=repeat_fine,
                        repeat_offense_fine=repeat_fine,
                        imprisonment=imprisonment,
                        license_points=license_points,
                        vehicle_seizure=seizure,
                        effective_date="2019-09-01"
                    )
                    db.add(penalty)
                    penalties_seeded += 1
                    
        db.commit()
        print(f"Seeded {penalties_seeded} violation penalties across states.")

        # 7. Traffic Rules Table
        rules_count = 0
        for code, state_name in state_data.items():
            state_id = gen_uuid(f"state_{code}")
            for rule in RULES_DATA:
                t_rule = TrafficRule(
                    rule_id=gen_uuid(f"rule_{code}_{rule['id']}"),
                    country_id=gen_uuid("country_IN"),
                    state_id=state_id,
                    category=rule["category"],
                    rule_title=rule["name"],
                    rule_description=rule["description"],
                    section_reference=rule["section"],
                    effective_date="2019-09-01",
                    source_url="https://morth.nic.in/"
                )
                db.add(t_rule)
                rules_count += 1
        db.commit()
        print(f"Seeded {rules_count} traffic rules definitions.")

        # 8. FAQ Knowledge (General FAQs)
        faq_data = [
            {"q": "Is helmet mandatory for pillion riders?", "a": "Yes, Section 129 of the Motor Vehicles Act makes helmets mandatory for both rider and pillion on two-wheelers conforming to BIS standards.", "cat": "Safety Equipment"},
            {"q": "What happens if I block an ambulance?", "a": "Blocking emergency vehicles like ambulances or fire engines is a severe offense under Section 194E, carrying a fine of \u20b910,000 and/or imprisonment.", "cat": "Traffic Violation"},
            {"q": "What is the penalty for driving without insurance?", "a": "Under Section 196, first offense carries a fine of \u20b92,000 and/or 3 months imprisonment. Subsequent offense carries \u20b94,000 fine and/or 3 months imprisonment.", "cat": "Documents"},
            {"q": "Is PUC mandatory for brand new vehicles?", "a": "New vehicles are exempt from PUC certification for the first one year from the date of registration. Thereafter, it must be renewed regularly.", "cat": "Documents"}
        ]
        for faq in faq_data:
            db.add(FAQKnowledge(
                faq_id=gen_uuid(f"faq_gen_{faq['q']}"),
                country_id=gen_uuid("country_IN"),
                state_id=gen_uuid("state_DL"), # Delhi as general baseline
                question=faq["q"],
                answer=faq["a"],
                category=faq["cat"]
            ))
        db.commit()
        print("Seeded base FAQ knowledge items.")

        # 9. Sync Versions Table
        sync_v = SyncVersion(
            version_id=str(uuid.uuid4()),
            data_type="rules",
            version_number="1.0.0",
            release_date=datetime.utcnow(),
            checksum=str(random.randint(100000, 999999))
        )
        db.add(sync_v)
        db.commit()
        
        # 10. Extract PDF specific data dynamically (LegalSource & State FAQs)
        extract_pdf_data(db)
        db.commit()

        # 11. Seed Compatibility Challans
        challans_seeded = 0
        for c in CHALLANS_DATA:
            state_code_upper = state_slugs.get(c["state_code"], "DL")
            
            issued_time = int(time.time() * 1000) - (random.randint(1, 10) * 24 * 3600 * 1000)
            deadline_time = issued_time + (60 * 24 * 3600 * 1000)
            
            item = c["items"][0]
            db_challan = Challan(
                id=str(uuid.uuid4()),
                challan_number=c["challan_number"],
                vehicle_number=c["vehicle_number"],
                violation_name=item["description"],
                location=f"{c['state_code'].title()} Highway Guard",
                amount=c["total_amount"],
                status=c["status"],
                issued_at=issued_time,
                deadline_at=deadline_time,
                section=item["section"],
                act="Motor Vehicles Act 2019",
                consequences=f"Compounded fine of \u20b9{c['total_amount']} pending under {item['section']}."
            )
            db.add(db_challan)
            challans_seeded += 1
        db.commit()
        print(f"Seeded {challans_seeded} compatibility challans.")

        print("All database tables seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
