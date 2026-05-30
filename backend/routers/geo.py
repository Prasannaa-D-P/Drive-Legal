from fastapi import APIRouter
from backend.schemas import GeoRequest, GeoResponse

router = APIRouter(
    prefix="/geo",
    tags=["Geofencing Radar"]
)

# Geofence bounding box mapping (matches laws_india.js coordinates)
GEOFENCE_DB = {
    "delhi": {
        "name": "Delhi (NCT)",
        "latMin": 28.40, "latMax": 28.88,
        "lngMin": 76.83, "lngMax": 77.34,
        "emergency_contacts": {
            "Traffic Police Helpline": "1095",
            "Emergency Helpline": "112",
            "Towing Services": "011-2584-4444"
        },
        "local_rules": [
            "Odd-Even Vehicle Scheme: Active periodically based on AQI air pollution directives. Fine for violation is ₹20,000.",
            "Strict lane discipline for buses and heavy vehicles. Bus lane violations carry ₹10,000 fine + court prosecution.",
            "Pillion rider helmet is strictly mandatory for all riders, including women (unless wearing a turban/Sikh).",
            "Tinted glasses on car windows (sun control films) are strictly prohibited. Light transmission must be >= 70%."
        ]
    },
    "karnataka": {
        "name": "Karnataka",
        "latMin": 11.50, "latMax": 18.50,
        "lngMin": 74.00, "lngMax": 78.50,
        "emergency_contacts": {
            "Bengaluru Traffic Helpline": "080-2286-3444",
            "Police Control Room": "100 / 112",
            "Ambulance Services": "108"
        },
        "local_rules": [
            "Pillion rider helmet is strictly mandatory across all cities in Karnataka (including Bengaluru).",
            "One-way rule violations are heavily monitored, especially in Bengaluru CBD. Fine is ₹1,000.",
            "Strict high-security registration plates (HSRP) rule implemented. Vehicles registered before 2019 must install HSRP.",
            "Defective/fancy license plates with regional language texts or design decals are fined at ₹1,000."
        ]
    },
    "maharashtra": {
        "name": "Maharashtra",
        "latMin": 15.60, "latMax": 22.00,
        "lngMin": 72.60, "lngMax": 80.90,
        "emergency_contacts": {
            "Mumbai Traffic Control Room": "022-2493-7747",
            "Highway Police Helpline": "98213-12131",
            "Emergency Services": "112"
        },
        "local_rules": [
            "Noise Pollution Rule: Use of pressure horns or honking in designated silent zones (schools, hospitals) carries a ₹2,000 fine.",
            "Reflector strips are mandatory on commercial trucks and school buses.",
            "Helmet compulsory for both rider and pillion in Mumbai and Pune. Strict enforcement with camera-based e-challan systems.",
            "Speed limits on Expressway (e.g. Mumbai-Pune Expressway) strictly set to 100 km/h. Fine for over-speeding is ₹2,000 for LMV."
        ]
    },
    "tamil_nadu": {
        "name": "Tamil Nadu",
        "latMin": 8.00, "latMax": 13.50,
        "lngMin": 76.00, "lngMax": 80.30,
        "emergency_contacts": {
            "Chennai Traffic Police": "044-2345-2362",
            "Police Emergency": "100 / 112",
            "Traffic Helpline": "103"
        },
        "local_rules": [
            "Strict zero-tolerance on drunk driving. Violators will have their vehicles seized and license recommended for suspension for 6 months.",
            "Rear seatbelts are mandatory for all occupants in four-wheelers.",
            "Helmet mandatory for two-wheeler riders. Pillion rider helmet strictly enforced in Chennai.",
            "Use of custom high-intensity LED headlights (unauthorized fittings) is strictly banned and fined."
        ]
    },
    "west_bengal": {
        "name": "West Bengal",
        "latMin": 21.50, "latMax": 27.30,
        "lngMin": 85.80, "lngMax": 89.80,
        "emergency_contacts": {
            "Kolkata Traffic Control": "033-2214-3644",
            "Police Emergency": "100 / 112",
            "Ambulance Services": "102"
        },
        "local_rules": [
            "'Safe Drive Save Life' campaign is strictly enforced. Two-wheeler riders without helmets are not allowed to refuel at petrol pumps ('No Helmet No Petrol').",
            "Two-wheelers are prohibited on certain flyovers in Kolkata during night hours (10:00 PM to 6:00 AM).",
            "Pillion rider helmet is mandatory.",
            "Speed limits inside Kolkata municipal area are highly restricted (typically 30-40 km/h in school/bazaar zones)."
        ]
    },
    "telangana": {
        "name": "Telangana",
        "latMin": 15.80, "latMax": 19.90,
        "lngMin": 77.20, "lngMax": 81.80,
        "emergency_contacts": {
            "Hyderabad Traffic Police": "040-2785-2482",
            "Police Control Room": "100 / 112",
            "Traffic Helpline / WhatsApp": "90102-03040"
        },
        "local_rules": [
            "E-Challan Point System: Accumulation of 12 penalty points leads to suspension of Driving License for a minimum of 1 year.",
            "Triple riding and helmetless driving are captured automatically via AI-based traffic cameras on junctions.",
            "Drunk driving carries immediate license impounding, mandatory counseling at Traffic Training Institutes, and court trial.",
            "Sound pollution: Altered silencer exhaust pipes (especially on cruiser bikes) are banned and seized on the spot."
        ]
    }
}

@router.post("/check", response_model=GeoResponse)
def check_geofence(coords: GeoRequest):
    lat = coords.latitude
    lng = coords.longitude
    
    for state_code, fence in GEOFENCE_DB.items():
        if fence["latMin"] <= lat <= fence["latMax"] and fence["lngMin"] <= lng <= fence["lngMax"]:
            return GeoResponse(
                matched=True,
                state_code=state_code,
                state_name=fence["name"],
                emergency_contacts=fence["emergency_contacts"],
                local_rules=fence["local_rules"]
            )
            
    # Default fallback (Delhi NCT) if coordinates don't hit a specific box
    default_fence = GEOFENCE_DB["delhi"]
    return GeoResponse(
        matched=False,
        state_code="delhi",
        state_name=default_fence["name"],
        emergency_contacts=default_fence["emergency_contacts"],
        local_rules=default_fence["local_rules"]
    )
