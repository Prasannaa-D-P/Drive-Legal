import os
import re
import tempfile
from typing import List, Dict, Any

try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

# Mapping keywords to violation database IDs
VIOLATION_KEYWORDS = {
    "no_helmet": [r"helmet", r"headgear", r"129", r"194d"],
    "triple_riding": [r"triple", r"3 riders", r"128", r"194c"],
    "no_seatbelt": [r"seatbelt", r"seat belt", r"194b"],
    "drunk_driving": [r"drunk", r"drink", r"alcohol", r"liquor", r"sobriety", r"185"],
    "speeding": [r"speed", r"speeding", r"overspeed", r"fast", r"183"],
    "red_light_jumping": [r"red light", r"signal", r"traffic light", r"184"],
    "using_mobile": [r"phone", r"mobile", r"handheld", r"184c"],
    "no_driving_license": [r"license", r"licence", r"driving license", r"dl", r"181"],
    "no_rc": [r"registration", r"rc book", r"unregistered", r"192"],
    "no_insurance": [r"insurance", r"third party", r"196"],
    "no_pucc": [r"puc", r"pucc", r"pollution", r"smoke", r"emission", r"190"],
    "obstructive_parking": [r"park", r"parking", r"no parking", r"122", r"177"],
    "emergency_vehicle_blocking": [r"ambulance", r"emergency", r"fire engine", r"194e"],
    "no_entry": [r"no entry", r"wrong way", r"one way", r"115"]
}

STATE_KEYWORDS = {
    "delhi": [r"delhi", r"nct", r"dl-", r"dl\d+"],
    "karnataka": [r"karnataka", r"bengaluru", r"bangalore", r"ka-", r"ka\d+"],
    "maharashtra": [r"maharashtra", r"mumbai", r"pune", r"mh-", r"mh\d+"],
    "tamil_nadu": [r"tamil nadu", r"chennai", r"coimbatore", r"tn-", r"tn\d+"],
    "west_bengal": [r"west bengal", r"kolkata", r"calcutta", r"wb-", r"wb\d+"],
    "telangana": [r"telangana", r"hyderabad", r"ts-", r"tg-", r"tg\d+", r"ts\d+"]
}

def parse_challan_text(text: str) -> Dict[str, Any]:
    """
    Parses OCR-extracted text using regex keyword matching to identify the state and violations.
    """
    normalized = text.lower()
    
    # 1. Match State
    detected_state = "delhi" # Default fallback
    for state_key, patterns in STATE_KEYWORDS.items():
        if any(re.search(pat, normalized) for pat in patterns):
            detected_state = state_key
            break
            
    # 2. Match Violations
    detected_violations = []
    for violation_id, patterns in VIOLATION_KEYWORDS.items():
        if any(re.search(pat, normalized) for pat in patterns):
            detected_violations.append(violation_id)
            
    # 3. Detect Vehicle Type
    detected_vehicle = "lmv"
    if any(re.search(pat, normalized) for pat in [r"bike", r"motorcycle", r"two-wheeler", r"scooter"]):
        detected_vehicle = "two_wheeler"
    elif any(re.search(pat, normalized) for pat in [r"truck", r"bus", r"heavy vehicle", r"hgv"]):
        detected_vehicle = "hgv"
    elif any(re.search(pat, normalized) for pat in [r"auto", r"three-wheeler"]):
        detected_vehicle = "three_wheeler"

    return {
        "state_code": detected_state,
        "vehicle_type": detected_vehicle,
        "violations": detected_violations,
        "confidence": 0.90 if len(detected_violations) > 0 else 0.50
    }

def read_challan_receipt(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Intakes uploaded files (images, PDFs, text) and extracts structured challan fields.
    Implements a robust fallback if Tesseract is not installed on the system.
    """
    extracted_text = ""
    
    # Try using PIL + Pytesseract if it's an image
    if HAS_OCR and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
        try:
            # Use a secure temporary file instead of a hardcoded path
            fd, temp_path = tempfile.mkstemp(suffix='.png', prefix='ocr_upload_')
            try:
                with os.fdopen(fd, 'wb') as f:
                    f.write(file_bytes)
                img = Image.open(temp_path)
                extracted_text = pytesseract.image_to_string(img)
            finally:
                # Always clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            print(f"[OCR Service] Pytesseract failed: {e}. Falling back to filename/text heuristics.")

    # Fallback/Heuristic: Check if file is plain text
    if not extracted_text:
        try:
            extracted_text = file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            pass

    # Heuristic: Inject filename keywords to make the user upload interactive
    # If the user uploads a file named "delhi_speeding_car.jpg", we parse the filename directly!
    filename_clean = filename.replace('_', ' ').replace('-', ' ').lower()
    extracted_text += " " + filename_clean

    # Parse and extract values
    result = parse_challan_text(extracted_text)
    
    # Add debug log
    print(f"[OCR Service] Scanned file '{filename}'. Matches found: {result['violations']} in state: {result['state_code']}")
    return result
