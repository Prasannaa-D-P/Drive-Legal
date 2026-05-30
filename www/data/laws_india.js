// Indian Traffic Laws and Violations Database (Motor Vehicles Amendment Act, 2019)
// Designed for offline client-side query matching, compounding calculations, and geofencing radar.

const DRIVELEGAL_DATA = {
  metadata: {
    lastUpdated: "2026-05-29",
    baselineLegislation: "Central Motor Vehicles (Amendment) Act 2019",
    currency: "INR",
    currencySymbol: "₹"
  },
  
  // Base vehicles classification
  vehicleTypes: {
    two_wheeler: { name: "Two-Wheeler (Motorcycle/Scooter)", code: "2W" },
    three_wheeler: { name: "Three-Wheeler (Auto-rickshaw)", code: "3W" },
    lmv: { name: "Light Motor Vehicle (Car/Jeep/SUV)", code: "LMV" },
    hgv: { name: "Heavy Goods/Passenger Vehicle (Truck/Bus)", code: "HGV" },
    other: { name: "Other / Unspecified Vehicles", code: "OTH" }
  },

  // Central baseline laws / violations
  violations: [
    {
      id: "no_helmet",
      name: "Riding without Helmet",
      section: "Section 129 / 194D",
      category: "Safety Equipment",
      description: "Riding a two-wheeler without a protective headgear conforming to standards (BIS), or failure to secure it properly.",
      base_fines: {
        two_wheeler: 1000,
        three_wheeler: 0,
        lmv: 0,
        hgv: 0,
        other: 0
      },
      repeat_fines: {
        two_wheeler: 1000
      },
      penalties: "Fine of ₹1,000 and disqualification/suspension of Driving License for a period of 3 months.",
      court_only: false
    },
    {
      id: "triple_riding",
      name: "Triple Riding on Two-Wheeler",
      section: "Section 128 / 194C",
      category: "Safety Equipment",
      description: "Riding a two-wheeler with more than one pillion rider (carrying more than two persons in total).",
      base_fines: {
        two_wheeler: 1000,
        three_wheeler: 0,
        lmv: 0,
        hgv: 0,
        other: 0
      },
      repeat_fines: {
        two_wheeler: 1000
      },
      penalties: "Fine of ₹1,000 and disqualification of license for 3 months.",
      court_only: false
    },
    {
      id: "no_seatbelt",
      name: "Driving without Seatbelt",
      section: "Section 194B(1)",
      category: "Safety Equipment",
      description: "Operating a motor vehicle without wearing a safety seatbelt, or carrying passengers in the front seat who are not wearing a seatbelt.",
      base_fines: {
        two_wheeler: 0,
        three_wheeler: 0,
        lmv: 1000,
        hgv: 1000,
        other: 1000
      },
      repeat_fines: {
        lmv: 1000,
        hgv: 1000,
        other: 1000
      },
      penalties: "Fine of ₹1,000.",
      court_only: false
    },
    {
      id: "drunk_driving",
      name: "Drunk Driving / Driving under Influence",
      section: "Section 185",
      category: "Speeding & Driving",
      description: "Driving a vehicle with Blood Alcohol Concentration (BAC) exceeding 30 mg per 100 ml of blood, or under the influence of drugs.",
      base_fines: {
        two_wheeler: 10000,
        three_wheeler: 10000,
        lmv: 10000,
        hgv: 10000,
        other: 10000
      },
      repeat_fines: {
        two_wheeler: 15000,
        three_wheeler: 15000,
        lmv: 15000,
        hgv: 15000,
        other: 15000
      },
      penalties: "First Offense: Fine up to ₹10,000 and/or imprisonment up to 6 months. Subsequent Offense: Fine up to ₹15,000 and/or imprisonment up to 2 years.",
      court_only: true // Requires judicial magistrate summons, non-compoundable on the spot
    },
    {
      id: "speeding",
      name: "Over-speeding",
      section: "Section 183(1)",
      category: "Speeding & Driving",
      description: "Driving a motor vehicle in contravention of the speed limits set for that road/zone.",
      base_fines: {
        two_wheeler: 1000,
        three_wheeler: 1000,
        lmv: 1000,
        hgv: 2000,
        other: 1000
      },
      repeat_fines: {
        two_wheeler: 2000,
        three_wheeler: 2000,
        lmv: 2000,
        hgv: 4000,
        other: 2000
      },
      penalties: "LMV fine of ₹1,000 - ₹2,000. Medium/Heavy vehicles fine of ₹2,000 - ₹4,000. Subsequent offense triggers impounding of driving license.",
      court_only: false
    },
    {
      id: "red_light_jumping",
      name: "Jumping Traffic Red Light",
      section: "Section 184 (Dangerous Driving)",
      category: "Traffic Violation",
      description: "Failing to stop at a red traffic signal, causing danger to other road users.",
      base_fines: {
        two_wheeler: 1000,
        three_wheeler: 1000,
        lmv: 1000,
        hgv: 2000,
        other: 1000
      },
      repeat_fines: {
        two_wheeler: 2000,
        three_wheeler: 2000,
        lmv: 2000,
        hgv: 5000,
        other: 2000
      },
      penalties: "Fine of ₹1,000 to ₹5,000 and/or imprisonment for 6 months to 1 year, and license suspension.",
      court_only: false
    },
    {
      id: "using_mobile",
      name: "Using Mobile Handheld Device while Driving",
      section: "Section 184(c)",
      category: "Speeding & Driving",
      description: "Using a mobile phone or handheld communication device while operating a vehicle (except for navigation in a hands-free manner).",
      base_fines: {
        two_wheeler: 1000,
        three_wheeler: 1000,
        lmv: 5000,
        hgv: 5000,
        other: 5000
      },
      repeat_fines: {
        two_wheeler: 2000,
        three_wheeler: 2000,
        lmv: 10000,
        hgv: 10000,
        other: 10000
      },
      penalties: "Fine of ₹1,000 to ₹5,000 for first-time offense. Subsequent offense up to ₹10,000.",
      court_only: false
    },
    {
      id: "no_driving_license",
      name: "Driving Without License",
      section: "Section 181",
      category: "Documents",
      description: "Driving a motor vehicle on public roads without holding a valid, active driving license for that specific class of vehicle.",
      base_fines: {
        two_wheeler: 5000,
        three_wheeler: 5000,
        lmv: 5000,
        hgv: 5000,
        other: 5000
      },
      repeat_fines: {
        two_wheeler: 5000,
        three_wheeler: 5000,
        lmv: 5000,
        hgv: 5000,
        other: 5000
      },
      penalties: "Fine of ₹5,000 and/or imprisonment up to 3 months.",
      court_only: false
    },
    {
      id: "no_rc",
      name: "Driving Unregistered Vehicle (No RC)",
      section: "Section 192",
      category: "Documents",
      description: "Driving or using a motor vehicle without a valid registration certificate (RC).",
      base_fines: {
        two_wheeler: 5000,
        three_wheeler: 5000,
        lmv: 5000,
        hgv: 5000,
        other: 5000
      },
      repeat_fines: {
        two_wheeler: 10000,
        three_wheeler: 10000,
        lmv: 10000,
        hgv: 10000,
        other: 10000
      },
      penalties: "First offense: Fine up to ₹5,000. Subsequent offense: Fine up to ₹10,000 or imprisonment up to 1 year.",
      court_only: false
    },
    {
      id: "no_insurance",
      name: "Driving Without Insurance Cover",
      section: "Section 196",
      category: "Documents",
      description: "Operating a motor vehicle without a valid third-party insurance cover.",
      base_fines: {
        two_wheeler: 2000,
        three_wheeler: 2000,
        lmv: 2000,
        hgv: 4000,
        other: 2000
      },
      repeat_fines: {
        two_wheeler: 4000,
        three_wheeler: 4000,
        lmv: 4000,
        hgv: 4000,
        other: 4000
      },
      penalties: "First offense: Fine of ₹2,000 and/or imprisonment up to 3 months. Subsequent offense: Fine of ₹4,000 and/or imprisonment up to 3 months.",
      court_only: false
    },
    {
      id: "no_pucc",
      name: "Driving Without PUC Certificate",
      section: "Section 190(2)",
      category: "Documents",
      description: "Driving a vehicle violating safety and air pollution standards (not possessing a valid Pollution Under Control certificate).",
      base_fines: {
        two_wheeler: 10000,
        three_wheeler: 10000,
        lmv: 10000,
        hgv: 10000,
        other: 10000
      },
      repeat_fines: {
        two_wheeler: 10000,
        three_wheeler: 10000,
        lmv: 10000,
        hgv: 10000,
        other: 10000
      },
      penalties: "Fine of ₹10,000, up to 3 months imprisonment, and Driving License disqualification for 3 months.",
      court_only: false
    },
    {
      id: "obstructive_parking",
      name: "Wrong / Obstructive Parking",
      section: "Section 122 / 177",
      category: "Parking",
      description: "Parking a vehicle in a public place in a manner that causes or is likely to cause danger, obstruction, or undue inconvenience to other users.",
      base_fines: {
        two_wheeler: 500,
        three_wheeler: 500,
        lmv: 500,
        hgv: 1000,
        other: 500
      },
      repeat_fines: {
        two_wheeler: 1500,
        three_wheeler: 1500,
        lmv: 1500,
        hgv: 1500,
        other: 1500
      },
      penalties: "Fine of ₹500 for first offense, ₹1,500 for subsequent. Towing fees apply additionally depending on city.",
      court_only: false
    },
    {
      id: "emergency_vehicle_blocking",
      name: "Blocking Emergency Vehicles",
      section: "Section 194E",
      category: "Traffic Violation",
      description: "Failing to draw to the side of the road to allow free passage to fire service vehicles, ambulances, or other emergency vehicles.",
      base_fines: {
        two_wheeler: 10000,
        three_wheeler: 10000,
        lmv: 10000,
        hgv: 10000,
        other: 10000
      },
      repeat_fines: {
        two_wheeler: 10000,
        three_wheeler: 10000,
        lmv: 10000,
        hgv: 10000,
        other: 10000
      },
      penalties: "Fine of ₹10,000 and/or imprisonment up to 6 months.",
      court_only: false
    },
    {
      id: "no_entry",
      name: "Driving in No-Entry Zone / Against Traffic",
      section: "Section 115 / 194C / 177",
      category: "Traffic Violation",
      description: "Driving a vehicle into a designated 'No-Entry' zone or in a direction opposite to the flow of traffic (one-way violation).",
      base_fines: {
        two_wheeler: 1000,
        three_wheeler: 1000,
        lmv: 2000,
        hgv: 5000,
        other: 2000
      },
      repeat_fines: {
        two_wheeler: 2000,
        three_wheeler: 2000,
        lmv: 4000,
        hgv: 10000,
        other: 4000
      },
      penalties: "Compounding fine varies by state; baseline begins at ₹500-₹2,000 depending on vehicle size.",
      court_only: false
    }
  ],

  // State-specific amendments and local rules
  states: {
    delhi: {
      name: "Delhi (NCT)",
      code: "DL",
      emergency_contacts: {
        "Traffic Police Helpline": "1095",
        "Emergency Helpline": "112",
        "Towing Services": "011-2584-4444"
      },
      local_rules: [
        "Odd-Even Vehicle Scheme: Active periodically based on AQI air pollution directives. Fine for violation is ₹20,000.",
        "Strict lane discipline for buses and heavy vehicles. Bus lane violations carry ₹10,000 fine + court prosecution.",
        "Pillion rider helmet is strictly mandatory for all riders, including women (unless wearing a turban/Sikh).",
        "Tinted glasses on car windows (sun control films) are strictly prohibited. Light transmission must be >= 70% for wind shield/rear and >= 50% for side windows."
      ],
      // Overrides on the compounding fees (if different from baseline MVA)
      compounding_fees: {
        no_helmet: { two_wheeler: 1000 },
        triple_riding: { two_wheeler: 1000 },
        no_seatbelt: { lmv: 1000 },
        speeding: { two_wheeler: 1000, lmv: 1000, hgv: 2000 },
        red_light_jumping: { two_wheeler: 1000, lmv: 1000, hgv: 2000 },
        using_mobile: { two_wheeler: 1000, lmv: 5000, hgv: 5000 },
        no_driving_license: { all: 5000 },
        no_rc: { all: 5000 },
        no_insurance: { two_wheeler: 2000, lmv: 2000, hgv: 4000 },
        no_pucc: { all: 10000 },
        obstructive_parking: { two_wheeler: 500, lmv: 500, hgv: 1000 },
        no_entry: { two_wheeler: 1000, lmv: 2000, hgv: 5000 }
      },
      // Geofencing bounding box coordinates (Latitude, Longitude) for mock GPS simulation
      geofence: {
        latMin: 28.40,
        latMax: 28.88,
        lngMin: 76.83,
        lngMax: 77.34,
        description: "Delhi Capital Region (NCT)"
      }
    },
    karnataka: {
      name: "Karnataka",
      code: "KA",
      emergency_contacts: {
        "Bengaluru Traffic Helpline": "080-2286-3444",
        "Police Control Room": "100 / 112",
        "Ambulance Services": "108"
      },
      local_rules: [
        "Pillion rider helmet is strictly mandatory across all cities in Karnataka (including Bengaluru).",
        "One-way rule violations are heavily monitored, especially in Bengaluru CBD. Fine is ₹1,000.",
        "Strict high-security registration plates (HSRP) rule implemented. Vehicles registered before 2019 must install HSRP.",
        "Defective/fancy license plates with regional language texts or design decals are fined at ₹1,000."
      ],
      compounding_fees: {
        // Karnataka state compounding overrides (lower compound rates for safety equipment, but strict enforcement)
        no_helmet: { two_wheeler: 500 }, // Reduced compounding rate in KA
        triple_riding: { two_wheeler: 500 },
        no_seatbelt: { lmv: 500 },
        speeding: { two_wheeler: 1000, lmv: 1000, hgv: 2000 },
        red_light_jumping: { two_wheeler: 500, lmv: 1000, hgv: 2000 },
        using_mobile: { two_wheeler: 1500, lmv: 5000, hgv: 5000 },
        no_driving_license: { all: 5000 },
        no_rc: { all: 5000 },
        no_insurance: { two_wheeler: 1000, lmv: 2000, hgv: 4000 }, // Insurance first fine compound KA
        no_pucc: { all: 10000 },
        obstructive_parking: { two_wheeler: 1000, lmv: 1000, hgv: 2000 }, // Stricter parking fines in KA
        no_entry: { two_wheeler: 1000, lmv: 1000, hgv: 2000 }
      },
      geofence: {
        latMin: 11.50,
        latMax: 18.50,
        lngMin: 74.00,
        lngMax: 78.50,
        description: "Karnataka State (HQ Bengaluru at 12.97, 77.59)"
      }
    },
    maharashtra: {
      name: "Maharashtra",
      code: "MH",
      emergency_contacts: {
        "Mumbai Traffic Control Room": "022-2493-7747",
        "Highway Police Helpline": "98213-12131",
        "Emergency Services": "112"
      },
      local_rules: [
        "Noise Pollution Rule: Use of pressure horns or honking in designated silent zones (schools, hospitals) carries a ₹2,000 fine.",
        "Reflector strips are mandatory on commercial trucks and school buses.",
        "Helmet compulsory for both rider and pillion in Mumbai and Pune. Strict enforcement with camera-based e-challan systems.",
        "Speed limits on Expressway (e.g. Mumbai-Pune Expressway) strictly set to 100 km/h. Fine for over-speeding is ₹2,000 for LMV."
      ],
      compounding_fees: {
        no_helmet: { two_wheeler: 500 },
        triple_riding: { two_wheeler: 1000 },
        no_seatbelt: { lmv: 500 },
        speeding: { two_wheeler: 1000, lmv: 1000, hgv: 2000 },
        red_light_jumping: { two_wheeler: 500, lmv: 1000, hgv: 2000 },
        using_mobile: { two_wheeler: 1000, lmv: 1000, hgv: 2000 }, // lower compound rate for mobile in MH
        no_driving_license: { all: 5000 },
        no_rc: { all: 5000 },
        no_insurance: { two_wheeler: 2000, lmv: 2000, hgv: 4000 },
        no_pucc: { all: 10000 },
        obstructive_parking: { two_wheeler: 500, lmv: 500, hgv: 1000 },
        no_entry: { two_wheeler: 1000, lmv: 2000, hgv: 5000 }
      },
      geofence: {
        latMin: 15.60,
        latMax: 22.00,
        lngMin: 72.60,
        lngMax: 80.90,
        description: "Maharashtra State (HQ Mumbai at 18.96, 72.82)"
      }
    },
    tamil_nadu: {
      name: "Tamil Nadu",
      code: "TN",
      emergency_contacts: {
        "Chennai Traffic Police": "044-2345-2362",
        "Police Emergency": "100 / 112",
        "Traffic Helpline": "103"
      },
      local_rules: [
        "Strict zero-tolerance on drunk driving. Violators will have their vehicles seized and license recommended for suspension for 6 months.",
        "Rear seatbelts are mandatory for all occupants in four-wheelers.",
        "Helmet mandatory for two-wheeler riders. Pillion rider helmet strictly enforced in Chennai.",
        "Use of custom high-intensity LED headlights (unauthorized fittings) is strictly banned and fined."
      ],
      compounding_fees: {
        no_helmet: { two_wheeler: 1000 },
        triple_riding: { two_wheeler: 1000 },
        no_seatbelt: { lmv: 1000 },
        speeding: { two_wheeler: 1000, lmv: 1000, hgv: 2000 },
        red_light_jumping: { two_wheeler: 1000, lmv: 1000, hgv: 2000 },
        using_mobile: { two_wheeler: 1000, lmv: 5000, hgv: 5000 },
        no_driving_license: { all: 5000 },
        no_rc: { all: 5000 },
        no_insurance: { two_wheeler: 2000, lmv: 2000, hgv: 4000 },
        no_pucc: { all: 10000 },
        obstructive_parking: { two_wheeler: 500, lmv: 500, hgv: 1000 },
        no_entry: { two_wheeler: 1000, lmv: 2000, hgv: 5000 }
      },
      geofence: {
        latMin: 8.00,
        latMax: 13.50,
        lngMin: 76.00,
        lngMax: 80.30,
        description: "Tamil Nadu State (HQ Chennai at 13.08, 80.27)"
      }
    },
    west_bengal: {
      name: "West Bengal",
      code: "WB",
      emergency_contacts: {
        "Kolkata Traffic Control": "033-2214-3644",
        "Police Emergency": "100 / 112",
        "Ambulance Services": "102"
      },
      local_rules: [
        "'Safe Drive Save Life' campaign is strictly enforced. Two-wheeler riders without helmets are not allowed to refuel at petrol pumps ('No Helmet No Petrol').",
        "Two-wheelers are prohibited on certain flyovers in Kolkata during night hours (10:00 PM to 6:00 AM).",
        "Pillion rider helmet is mandatory.",
        "Speed limits inside Kolkata municipal area are highly restricted (typically 30-40 km/h in school/bazaar zones). Speed cameras are widely deployed."
      ],
      compounding_fees: {
        no_helmet: { two_wheeler: 1000 },
        triple_riding: { two_wheeler: 1000 },
        no_seatbelt: { lmv: 1000 },
        speeding: { two_wheeler: 1000, lmv: 1000, hgv: 2000 },
        red_light_jumping: { two_wheeler: 1000, lmv: 1000, hgv: 2000 },
        using_mobile: { two_wheeler: 2000, lmv: 2000, hgv: 5000 },
        no_driving_license: { all: 5000 },
        no_rc: { all: 5000 },
        no_insurance: { two_wheeler: 2000, lmv: 2000, hgv: 4000 },
        no_pucc: { all: 10000 },
        obstructive_parking: { two_wheeler: 500, lmv: 500, hgv: 1000 },
        no_entry: { two_wheeler: 2000, lmv: 2000, hgv: 5000 } // high fine for no-entry in WB
      },
      geofence: {
        latMin: 21.50,
        latMax: 27.30,
        lngMin: 85.80,
        lngMax: 89.80,
        description: "West Bengal State (HQ Kolkata at 22.57, 88.36)"
      }
    },
    telangana: {
      name: "Telangana",
      code: "TG", // Previously TS
      emergency_contacts: {
        "Hyderabad Traffic Police": "040-2785-2482",
        "Police Control Room": "100 / 112",
        "Traffic Helpline / WhatsApp": "90102-03040"
      },
      local_rules: [
        "E-Challan Point System: Accumulation of 12 penalty points leads to suspension of Driving License for a minimum of 1 year.",
        "Triple riding and helmetless driving are captured automatically via AI-based traffic cameras on junctions.",
        "Drunk driving carries immediate license impounding, mandatory counseling at Traffic Training Institutes, and court trial.",
        "Sound pollution: Altered silencer exhaust pipes (especially on cruiser bikes) are banned and seized on the spot."
      ],
      compounding_fees: {
        no_helmet: { two_wheeler: 200 }, // lower spot compound fine in Telangana, but point addition applies
        triple_riding: { two_wheeler: 1000 },
        no_seatbelt: { lmv: 250 }, // lower compound rate
        speeding: { two_wheeler: 1000, lmv: 1000, hgv: 2000 },
        red_light_jumping: { two_wheeler: 1000, lmv: 1000, hgv: 2000 },
        using_mobile: { two_wheeler: 1000, lmv: 2000, hgv: 5000 },
        no_driving_license: { all: 5000 },
        no_rc: { all: 5000 },
        no_insurance: { two_wheeler: 2000, lmv: 2000, hgv: 4000 },
        no_pucc: { all: 10000 },
        obstructive_parking: { two_wheeler: 200, lmv: 200, hgv: 500 }, // lower baseline
        no_entry: { two_wheeler: 200, lmv: 1000, hgv: 2000 }
      },
      geofence: {
        latMin: 15.80,
        latMax: 19.90,
        lngMin: 77.20,
        lngMax: 81.80,
        description: "Telangana State (HQ Hyderabad at 17.38, 78.48)"
      }
    }
  }
};
