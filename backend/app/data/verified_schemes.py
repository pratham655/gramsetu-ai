from typing import List, Dict, Any

# Official, verified government schemes with deterministic eligibility criteria
VERIFIED_SCHEMES_SEED: List[Dict[str, Any]] = [
    {
        "id": "pm-kisan-001",
        "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "localized_names": {
            "kn": "ಪಿಎಂ ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ (PM-KISAN)",
            "hi": "पीएम किसान सम्मान निधि (PM-KISAN)",
            "en": "PM-KISAN Samman Nidhi",
        },
        "aliases": [
            "pm kisan", "pm-kisan", "pmkisan", "kisan samman", "kisan scheme", "kisan yojana", "kisan 6000",
            "ಪಿಎಂ ಕಿಸಾನ್", "ಕಿಸಾನ್ ಸಮ್ಮಾನ್", "ಕಿಸಾನ್ ಯೋಜನೆ", "ರೈತರ 6000",
            "पीएम किसान", "किसान सम्मान निधि", "किसान योजना", "किसान 6000"
        ],
        "short_description": "Central income support initiative providing ₹6,00,0 per year to landholding farmer families.",
        "detailed_description": (
            "PM-KISAN is a Central Sector Scheme providing income support to all landholding farmers' "
            "families in the country to cultivate agricultural and allied activities as well as domestic needs. "
            "Financial benefit of ₹6,000/- per annum is provided in three equal installments of ₹2,000/- each."
        ),
        "benefits": [
            "Direct income support of ₹6,000 per year transferred in 3 equal installments of ₹2,000",
            "100% Direct Benefit Transfer (DBT) into Aadhaar-seeded bank accounts",
            "Covers expenses for agricultural inputs, seeds, fertilizers, and domestic needs"
        ],
        "state": None,  # Central scheme
        "category": "Agriculture",
        "occupation": "farmer",
        "official_source_url": "https://pmkisan.gov.in",
        "application_url": "https://pmkisan.gov.in/RegistrationFormNew.aspx",
        "required_documents": [
            "Aadhaar Card",
            "Proof of Agricultural Land Ownership (ROR / Khasra / Khatauni)",
            "Aadhaar-seeded Bank Account Passbook",
            "Active Mobile Number linked with Aadhaar"
        ],
        "active": True,
        "rules": [
            {
                "field": "occupation",
                "operator": "in",
                "value": "farmer,agriculture,cultivator",
                "description": "Applicant must be a farmer or engaged in agriculture."
            },
            {
                "field": "landholding",
                "operator": "greater_than",
                "value": "0.0",
                "description": "Applicant family must possess cultivable agricultural land."
            }
        ]
    },
    {
        "id": "pmay-g-002",
        "name": "Pradhan Mantri Awas Yojana - Gramin (PMAY-G)",
        "localized_names": {
            "kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಆವಾಸ್ ಯೋಜನೆ - ಗ್ರಾಮೀಣ (PMAY-G)",
            "hi": "प्रधानमंत्री आवास योजना - ग्रामीण (PMAY-G)",
            "en": "Pradhan Mantri Awas Yojana - Gramin (PMAY-G)",
        },
        "aliases": [
            "pmay", "pmay-g", "pmayg", "awas yojana", "pm awas", "rural housing", "gramin awas", "house grant", "120000 house",
            "ಪಿಎಂ ಆವಾಸ್", "ಆವಾಸ್ ಯೋಜನೆ", "ಮನೆ ಯೋಜನೆ", "ಗ್ರಾಮೀಣ ವಸತಿ", "ಪ್ರಧಾನ ಮಂತ್ರಿ ಆವಾಸ್",
            "पीएम आवास", "आवास योजना", "पीएम आवास योजना", "ग्रामीण आवास", "मकान योजना"
        ],
        "short_description": "Rural housing scheme providing financial aid to homeless households and those living in kutcha houses.",
        "detailed_description": (
            "PMAY-G aims to provide a pucca house with basic amenities to all rural families who are homeless "
            "or living in kutcha or dilapidated houses. Beneficiaries are selected using housing deprivation parameters "
            "derived from Socio-Economic and Caste Census (SECC) data validated by the Gram Sabha."
        ),
        "benefits": [
            "Financial grant of ₹1,20,000 in plain areas and ₹1,30,000 in hilly/difficult areas",
            "Unskilled labour wages for 90-95 person-days under MGNREGA (approx ₹18,000 - ₹24,000)",
            "Additional assistance of ₹12,000 for toilet construction under Swachh Bharat Mission - Gramin"
        ],
        "state": None,
        "category": "Housing & Rural Development",
        "occupation": None,
        "official_source_url": "https://pmayg.nic.in",
        "application_url": "https://awaassoft.nic.in",
        "required_documents": [
            "Aadhaar Card",
            "BPL Ration Card / SECC 2011 Verification Document",
            "Bank Account Passbook (Aadhaar linked)",
            "Land / Homestead ownership document or allotment order",
            "MGNREGA Job Card (for labour component)"
        ],
        "active": True,
        "rules": [
            {
                "field": "bpl",
                "operator": "equals",
                "value": "true",
                "description": "Applicant must belong to Below Poverty Line (BPL) or SECC deprivation list."
            },
            {
                "field": "income",
                "operator": "less_than_or_equal",
                "value": "300000",
                "description": "Annual household income must not exceed ₹3,00,000."
            }
        ]
    },
    {
        "id": "pmmvy-003",
        "name": "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
        "localized_names": {
            "kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಮಾತೃ ವಂದನಾ ಯೋಜನೆ (PMMVY)",
            "hi": "प्रधानमंत्री मातृ वंदना योजना (PMMVY)",
            "en": "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
        },
        "aliases": [
            "pmmvy", "matru vandana", "matritva", "maternity benefit", "pregnancy scheme", "pregnant women", "mother scheme", "5000 pregnancy",
            "ಮಾತೃ ವಂದನಾ", "ಗರ್ಭಿಣಿ ಯೋಜನೆ", "ತಾಯಿ ಯೋಜನೆ", "ಮಾತೃತ್ವ ಯೋಜನೆ",
            "मातृ वंदना", "मातृत्व योजना", "गर्भवती सहायता", "मातृ वंदना योजना"
        ],
        "short_description": "Maternity benefit cash incentive for pregnant women and lactating mothers.",
        "detailed_description": (
            "PMMVY is a Centrally Sponsored maternity benefit scheme providing partial compensation for the wage "
            "loss in terms of cash incentives so that the woman can take adequate rest before and after delivery "
            "of the first living child, promoting improved health-seeking behavior."
        ),
        "benefits": [
            "Direct cash incentive of ₹5,000 in installments upon timely registration and institutional delivery",
            "Additional ₹6,000 for second child if the newborn is a girl child",
            "Improves maternal and infant nutrition and covers initial child immunization"
        ],
        "state": None,
        "category": "Women & Child Development",
        "occupation": None,
        "official_source_url": "https://wcd.nic.in/schemes/pradhan-mantri-matru-vandana-yojana",
        "application_url": "https://pmmvy.wcd.gov.in",
        "processing_timeline": {
            "expected_days": 30,
            "description": "Installments disbursed within 30 days of stage milestone verification via DBT",
            "is_verified": True
        },
        "required_documents": [
            "Mother's Aadhaar Card",
            "Husband's Aadhaar Card",
            "Mother and Child Protection (MCP) Card",
            "Aadhaar-linked Bank / Post Office Account Passbook"
        ],
        "active": True,
        "rules": [
            {
                "field": "gender",
                "operator": "equals",
                "value": "female",
                "description": "Beneficiary must be female (pregnant or lactating mother)."
            },
            {
                "field": "age",
                "operator": "greater_than_or_equal",
                "value": "19",
                "description": "Mother must be 19 years of age or older at the time of pregnancy."
            },
            {
                "field": "income",
                "operator": "less_than_or_equal",
                "value": "800000",
                "description": "Family income must be below ₹8,00,000 per annum."
            }
        ]
    },
    {
        "id": "pm-jay-004",
        "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
        "localized_names": {
            "kn": "ಆಯುಷ್ಮಾನ್ ಭಾರತ್ - ಪಿಎಂ ಜನ ಆರೋಗ್ಯ ಯೋಜನೆ (PM-JAY)",
            "hi": "आयुष्मान भारत - पीएम जन आरोग्य योजना (PM-JAY)",
            "en": "Ayushman Bharat - PM-JAY",
        },
        "aliases": [
            "pmjay", "pm-jay", "ayushman", "ayushman bharat", "health card", "5 lakh health", "health insurance", "arogya yojana", "ayushman card",
            "ಆಯುಷ್ಮಾನ್ ಭಾರತ್", "ಆಯುಷ್ಮಾನ್", "ಆರೋಗ್ಯ ಕಾರ್ಡ್", "5 ಲಕ್ಷ ಚಿಕಿತ್ಸೆ", "ಜನ ಆರೋಗ್ಯ",
            "आयुष्मान भारत", "आयुष्मान", "स्वास्थ्य कार्ड", "5 लाख इलाज", "जन आरोग्य योजना", "आयुष्मान कार्ड"
        ],
        "short_description": "World's largest government-funded health assurance scheme providing ₹5 Lakh coverage per family.",
        "detailed_description": (
            "PM-JAY provides health cover of ₹5,00,000 per family per year for secondary and tertiary care "
            "hospitalization across empaneled public and private hospitals in India. It is completely cashless "
            "and paperless at the point of service delivery."
        ),
        "benefits": [
            "Cashless health insurance coverage up to ₹5,00,000 per family per year",
            "Covers medical examination, consultation, hospital accommodation, ICU, surgical procedures, and diagnostic tests",
            "Pre-hospitalization coverage up to 3 days and post-hospitalization medications for 15 days"
        ],
        "state": None,
        "category": "Health & Social Protection",
        "occupation": None,
        "official_source_url": "https://nha.gov.in/PM-JAY",
        "application_url": "https://beneficiary.nha.gov.in",
        "processing_timeline": {
            "expected_days": 1,
            "description": "Ayushman Card generated instantly upon biometric eKYC verification at kiosk",
            "is_verified": True
        },
        "required_documents": [
            "Aadhaar Card or Government-issued Photo ID",
            "Ration Card / BPL Card / PM-JAY Family ID letter",
            "Registered Mobile Number"
        ],
        "active": True,
        "rules": [
            {
                "field": "bpl",
                "operator": "equals",
                "value": "true",
                "description": "Must belong to BPL / economically vulnerable category identified in SECC."
            }
        ]
    },
    {
        "id": "raitha-vidya-005",
        "name": "Karnataka Raitha Vidya Nidhi Scholarship",
        "localized_names": {
            "kn": "ಮುಖ್ಯಮಂತ್ರಿ ರೈತ ವಿದ್ಯಾನಿಧಿ ಯೋಜನೆ",
            "hi": "मुख्यमंत्री रायथ विद्या निधि योजना",
            "en": "Chief Minister Raitha Vidya Nidhi Scholarship",
        },
        "aliases": [
            "raitha vidya", "vidya nidhi", "vidyanidhi", "farmer scholarship", "farmer children scholarship", "karnataka scholarship",
            "ರೈತ ವಿದ್ಯಾನಿಧಿ", "ವಿದ್ಯಾನಿಧಿ", "ರೈತರ ವಿದ್ಯಾರ್ಥಿವೇತನ", "ರೈತರ ಮಕ್ಕಳಿಗೆ ಸ್ಕಾಲರ್‌ಶಿಪ್",
            "रायथ विद्या निधि", "विद्या निधि", "किसान छात्रवृत्ति", "कर्नाटक छात्रवृत्ति"
        ],
        "short_description": "State education scholarship for the children of farmers in Karnataka.",
        "detailed_description": (
            "Raitha Vidya Nidhi was launched by the Government of Karnataka to provide annual financial "
            "scholarships to the children of registered farmers to encourage them to pursue higher education "
            "and vocational courses after Class 10."
        ),
        "benefits": [
            "Annual scholarship of ₹2,000 to ₹11,000 depending on course and gender (higher for girl students)",
            "Disbursed directly via DBT into student's bank account",
            "Covers PUC, ITI, Diploma, Degree, Postgraduate, and Professional courses (Medical, Engineering)"
        ],
        "state": "Karnataka",
        "category": "Education & Agriculture",
        "occupation": "farmer",
        "official_source_url": "https://raitamitra.karnataka.gov.in",
        "application_url": "https://ssp.postmatric.karnataka.gov.in",
        "required_documents": [
            "Farmer Identification Number (FID) / Kutumba ID",
            "Student's Aadhaar Card",
            "Parent / Guardian Farmer Aadhaar Card",
            "College Admission / Fee Receipt with Student ID",
            "Aadhaar-seeded Bank Account Passbook"
        ],
        "active": True,
        "rules": [
            {
                "field": "state",
                "operator": "in",
                "value": "Karnataka,karnataka",
                "description": "Applicant must be a resident of Karnataka state."
            },
            {
                "field": "occupation",
                "operator": "in",
                "value": "farmer,agriculture,cultivator",
                "description": "Parent or guardian must be a registered farmer."
            }
        ]
    },
    {
        "id": "ration-card-006",
        "name": "National Food Security Act (NFSA) / Ration Card Service",
        "localized_names": {
            "kn": "ರೇಷನ್ ಕಾರ್ಡ್ (ಪಡಿತರ ಚೀಟಿ - NFSA)",
            "hi": "राशन कार्ड सेवा (NFSA)",
            "en": "National Food Security Act (NFSA) / Ration Card Service",
        },
        "aliases": [
            "ration card", "ration", "rationcard", "nfsa", "bpl card", "aay card", "antyodaya", "phh card", "apl card",
            "apply for ration card", "food card", "ration card apply", "ration card application", "ration card details",
            "ರೇಷನ್ ಕಾರ್ಡ್", "ರೇಷನ್", "ಪಡಿತರ ಚೀಟಿ", "ಪಡಿತರ ಚೀಟಿ ಅರ್ಜಿ", "ಬಿಪಿಎಲ್ ಕಾರ್ಡ್", "ಆಹಾರ ಭದ್ರತೆ", "ಅನ್ನಭಾಗ್ಯ",
            "ರಾಷನ್ ಕಾರ್ಡ್", "ರೇಶನ್", "ರೇಶನ್ ಕಾರ್ಡ್", "ರೇಷನ್‌ಕಾರ್ಡ್", "ರೇಶನ್ ಕಾರ್ಡ್ ಅರ್ಜಿ", "ರೇಷನ್ ಕಾರ್ಡ್ ಅರ್ಜಿ",
            "राशन कार्ड", "राशन", "राशनकार्ड", "बीपीएल राशन कार्ड", "खाद्य सुरक्षा", "राशन कार्ड आवेदन", "राशन कार्ड कैसे बनवाएं",
            "ration cardulu", "ration cardu", "ration patra"
        ],
        "short_description": "Subsidized foodgrains and food security entitlement card for eligible households (BPL / Antyodaya / APL).",
        "detailed_description": (
            "The National Food Security Act (NFSA) / Public Distribution System provides subsidized and free foodgrains "
            "(Rice, Wheat, Coarse grains) to eligible households through fair price shops. Ration cards are classified "
            "into Antyodaya Anna Yojana (AAY - poorest of poor), Priority Household (PHH / BPL), and Non-Priority Household (NPHH / APL)."
        ),
        "benefits": [
            "Subsidized or free monthly foodgrains (Rice, Wheat, Coarse grains) per member under NFSA / PMGKAY",
            "Serves as essential statutory proof of residence, family composition, and economic status",
            "Mandatory prerequisite document for government welfare schemes including PMAY-G and PM-JAY"
        ],
        "state": None,
        "category": "Food Security & Public Distribution",
        "occupation": None,
        "official_source_url": "https://nfsa.gov.in",
        "application_url": "https://ahara.kar.nic.in",
        "processing_timeline": {
            "expected_days": 30,
            "description": "Card issued within 30 statutory working days post Aadhaar e-KYC and field verification",
            "is_verified": True
        },
        "required_documents": [
            "Aadhaar Card of all family members",
            "Proof of Residence (Electricity Bill / Water Bill / House Tax Receipt)",
            "Income Certificate (issued by Revenue Authority / Tahsildar for BPL/AAY)",
            "Active Mobile Number linked with Aadhaar",
            "Passport-size Photograph of Head of Family (Female head of household)"
        ],
        "active": True,
        "rules": [
            {
                "field": "bpl",
                "operator": "equals",
                "value": "true",
                "description": "Applicant family must belong to BPL or economically weaker household for subsidized category."
            },
            {
                "field": "income",
                "operator": "less_than_or_equal",
                "value": "120000",
                "description": "Annual household income must not exceed ₹1,20,000 for Priority (BPL / PHH) ration card."
            }
        ]
    }
]

