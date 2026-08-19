import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.data.verified_schemes import VERIFIED_SCHEMES_SEED
from app.schemas.parchaa import (
    ParchaaSchemeSummary,
    ParchaaCitizenProfile,
    ParchaaDocumentItem,
    ParchaaOffice,
    ParchaaTimeline,
    ParchaaApplicationInfo,
    DocumentStatusEnum,
)

# Verified official scheme metadata registry (offices, processing guidelines, enclosures)
# Strictly grounded in statutory guidelines; explicit unverified fallback where not in database
VERIFIED_SCHEME_METADATA: Dict[str, Dict[str, Any]] = {
    "pm-kisan-001": {
        "target_beneficiaries": "All landholding farmer families with cultivable land in their names",
        "application_channel": "Online Portal (pmkisan.gov.in) or Nearest Common Service Centre (CSC) / Village Gram Panchayat",
        "administrative_office": {
            "office_name": "District Agriculture Officer / PM-KISAN Nodal Office",
            "department": "Department of Agriculture & Farmers Welfare, Ministry of Agriculture",
            "address": "Krishi Bhavan / District Agriculture Complex",
            "contact_info": "PM-KISAN Helpdesk: 155261 / 011-24300606",
            "is_verified": True,
        },
        "processing_timeline": {
            "expected_days": None,
            "timeline_description": "Installments disbursed every 4 months (April-July, August-November, December-March) after state validation",
            "is_verified": True,
        },
        "enclosures": [
            "Self-attested copy of Aadhaar Card",
            "Certified Copy of Land Record (ROR / Khasra / Khatauni / Pahani)",
            "First page copy of Aadhaar-seeded Active Bank Account Passbook",
            "Self-declaration of landholding and eligibility"
        ],
        "process_steps": [
            "1. Verify Aadhaar seeding with active bank account and active mobile number.",
            "2. Access Farmer Corner on pmkisan.gov.in or visit local CSC Kendra.",
            "3. Fill landholding survey numbers and upload certified Land RoR document.",
            "4. Submit application for Patwari / District Nodal Officer state verification.",
            "5. Track DBT installment credit status using Aadhaar number on official portal."
        ]
    },
    "pmay-g-002": {
        "target_beneficiaries": "Rural houseless families and households living in zero, one or two room kutcha houses",
        "application_channel": "Gram Sabha Validation / Awaas+ Portal through Gram Panchayat Panchayat Secretary",
        "administrative_office": {
            "office_name": "Block Development Office / Gram Panchayat Office",
            "department": "Department of Rural Development, Ministry of Rural Development",
            "address": "Taluk / Block Panchayat Office",
            "contact_info": "PMAY-G Toll Free: 1800-11-6446",
            "is_verified": True,
        },
        "processing_timeline": {
            "expected_days": None,
            "timeline_description": "Grant released in 3 geo-tagged construction stages over house completion period",
            "is_verified": True,
        },
        "enclosures": [
            "Aadhaar card copies of all adult family members",
            "BPL Ration Card / SECC 2011 Household Identification Document",
            "Bank passbook copy with IFSC and Aadhaar DBT consent",
            "Land / Homestead possession certificate or Gram Sabha allotment order",
            "Active MGNREGA Job Card for unskilled labour wage credit"
        ],
        "process_steps": [
            "1. Verification of name in SECC Priority List / Awaas+ waitlist by Gram Sabha.",
            "2. Geo-tagging of existing kutcha house location by Panchayat Secretary.",
            "3. Sanction order generation and 1st installment (₹40,000) credit via DBT.",
            "4. Construction up to lintel level and 2nd stage geo-tag verification.",
            "5. Final completion inspection, toilet verification, and final disbursement."
        ]
    },
    "pmmvy-003": {
        "target_beneficiaries": "Pregnant Women and Lactating Mothers (PW&LM) for first living child (and second child if girl)",
        "application_channel": "Anganwadi Centre (AWC) / Government Health Facility or pmmvy.wcd.gov.in",
        "administrative_office": {
            "office_name": "Child Development Project Officer (CDPO) / Anganwadi Centre",
            "department": "Ministry of Women & Child Development",
            "address": "Sector Anganwadi Center / Taluk CDPO Office",
            "contact_info": "PMMVY Helpdesk: 011-23382393",
            "is_verified": True,
        },
        "processing_timeline": {
            "expected_days": 30,
            "timeline_description": "Installments disbursed within 30 days of stage milestone verification via DBT",
            "is_verified": True,
        },
        "enclosures": [
            "Mother's Aadhaar Card copy (Mandatory)",
            "Husband's Aadhaar Card copy (if applicable)",
            "Mother and Child Protection (MCP) Card with ANC registration dates",
            "Institutional Child Birth Certificate (for 2nd installment)",
            "Aadhaar-linked single Bank / Post Office account passbook copy"
        ],
        "process_steps": [
            "1. Register pregnancy at nearest Anganwadi Centre within 570 days of LMP.",
            "2. Submit Form 1A along with MCP Card showing at least one ANC checkup.",
            "3. Form 1B submission after institutional delivery and birth registration.",
            "4. Form 1C submission after child receives first cycle of OPV, BCG, DPT/Penta vaccines.",
            "5. Direct DBT credit into mother's verified bank account."
        ]
    },
    "pm-jay-004": {
        "target_beneficiaries": "Deprived rural and urban occupational worker families identified under SECC 2011",
        "application_channel": "Ayushman Mitra at Empaneled Hospital / CSC Kendra / beneficiary.nha.gov.in",
        "administrative_office": {
            "office_name": "National Health Authority (NHA) / District Ayushman Cell",
            "department": "Ministry of Health and Family Welfare",
            "address": "District Civil Hospital / NHA State Health Agency",
            "contact_info": "National Toll-Free Helpline: 14555",
            "is_verified": True,
        },
        "processing_timeline": {
            "expected_days": 1,
            "timeline_description": "Ayushman Card generated instantly upon biometric eKYC verification at kiosk",
            "is_verified": True,
        },
        "enclosures": [
            "Aadhaar Card of the beneficiary",
            "Ration Card / PM-JAY Family Verification letter / State Health Card",
            "Active registered mobile phone for OTP verification"
        ],
        "process_steps": [
            "1. Check family eligibility on beneficiary.nha.gov.in using Ration Card / Aadhaar.",
            "2. Visit nearest CSC Kendra or Ayushman Helpdesk at empaneled hospital.",
            "3. Complete Aadhaar e-KYC (Biometric fingerprint or mobile OTP).",
            "4. Download and print Ayushman PVC card with Unique Ayushman ID.",
            "5. Avail cashless treatment up to ₹5,00,000 per family per year."
        ]
    },
    "raitha-vidya-005": {
        "target_beneficiaries": "Children of registered farmers in Karnataka pursuing post-matric / higher education",
        "application_channel": "State Scholarship Portal (SSP Karnataka) - ssp.postmatric.karnataka.gov.in",
        "administrative_office": {
            "office_name": "Department of Agriculture / District Joint Director of Agriculture",
            "department": "Government of Karnataka Agriculture Department",
            "address": "Raitha Samparka Kendra (RSK) / Taluk Agriculture Office",
            "contact_info": "SSP Karnataka Helpline: 1902 / 080-35254757",
            "is_verified": True,
        },
        "processing_timeline": {
            "expected_days": 45,
            "timeline_description": "Scholarship disbursed annually after college e-attestation and Kutumba FID validation",
            "is_verified": True,
        },
        "enclosures": [
            "Student Aadhaar Card copy",
            "Parent / Farmer Aadhaar Card with Farmer Identification Number (FID)",
            "College Admission Fee Receipt / Study Certificate with Student USN/Roll No",
            "Student's Aadhaar-seeded Bank Account Passbook copy"
        ],
        "process_steps": [
            "1. Ensure Parent Farmer has active FID on Bhoomi / Kutumba portal.",
            "2. Create Student Account on Karnataka State Scholarship Portal (SSP).",
            "3. Enter Student Aadhaar, College E-Attestation ID, and Parent FID number.",
            "4. Submit online application; college principal completes digital verification.",
            "5. Scholarship credited directly into student's DBT bank account."
        ]
    },
    "ration-card-006": {
        "target_beneficiaries": "Rural and urban households seeking food security entitlement (BPL / PHH / AAY / APL)",
        "application_channel": "Seva Sindhu / Ahara Portal (ahara.kar.nic.in) or Nearest Gram One / CSC / Food & Civil Supplies Office",
        "administrative_office": {
            "office_name": "Food & Civil Supplies Inspector / Taluk Food Office",
            "department": "Department of Food, Civil Supplies and Consumer Affairs",
            "address": "Taluk Administrative Complex / Food Inspector Office",
            "contact_info": "Food & Civil Supplies Toll-Free: 1967 / 1800-425-9339",
            "is_verified": True,
        },
        "processing_timeline": {
            "expected_days": 30,
            "timeline_description": "Card issued within 30 statutory working days post Aadhaar e-KYC and field verification",
            "is_verified": True,
        },
        "enclosures": [
            "Self-attested copies of Aadhaar cards of all family members",
            "Certified copy of latest Electricity Bill / House Tax receipt for residential proof",
            "Income Certificate issued by Tahsildar / Revenue Department",
            "Passport-size photograph of female head of household"
        ],
        "process_steps": [
            "1. Collect Aadhaar details and mobile numbers of all household members.",
            "2. Submit online application at Gram One / Seva Sindhu or state Food portal (ahara.kar.nic.in).",
            "3. Biometric / OTP e-KYC authentication of all family members.",
            "4. Field inquiry and spot verification by Food Inspector / Revenue Officer.",
            "5. Approval by Tahsildar / Food Shirastedar and e-Ration card generation for download."
        ]
    }
}



def mask_sensitive_id(value: Optional[str], id_type: str = "aadhaar") -> Optional[str]:
    """
    Masks sensitive identifiers like Aadhaar, Bank account, or PAN to protect citizen privacy.
    Never exposes raw PII.
    """
    if not value or not isinstance(value, str):
        return None
    
    clean_val = re.sub(r'[\s\-]', '', value.strip())
    
    if id_type == "aadhaar":
        if len(clean_val) >= 12:
            return f"XXXX-XXXX-{clean_val[-4:]}"
        elif len(clean_val) >= 4:
            return f"XXXX-{clean_val[-4:]}"
        return "XXXX-XXXX-XXXX"
        
    elif id_type == "bank":
        if len(clean_val) >= 4:
            return f"XXXXXX{clean_val[-4:]}"
        return "XXXXXX"
        
    return clean_val


def sanitize_citizen_profile(profile_dict: Optional[Dict[str, Any]]) -> Optional[ParchaaCitizenProfile]:
    """
    Parses and sanitizes citizen profile dictionary into a safe ParchaaCitizenProfile object.
    Masks any sensitive fields.
    """
    if not profile_dict:
        return None

    aadhaar_raw = profile_dict.get("aadhaar_number") or profile_dict.get("aadhaar") or profile_dict.get("aadhaar_masked")
    bank_raw = profile_dict.get("bank_account") or profile_dict.get("account_number") or profile_dict.get("bank_account_masked")

    masked_aadhaar = mask_sensitive_id(aadhaar_raw, "aadhaar") if aadhaar_raw else None
    masked_bank = mask_sensitive_id(bank_raw, "bank") if bank_raw else None

    return ParchaaCitizenProfile(
        name=profile_dict.get("name") or profile_dict.get("full_name") or profile_dict.get("citizen_name"),
        state=profile_dict.get("state"),
        district=profile_dict.get("district"),
        occupation=profile_dict.get("occupation"),
        age=profile_dict.get("age"),
        gender=profile_dict.get("gender"),
        income=profile_dict.get("income"),
        landholding=profile_dict.get("landholding"),
        category=profile_dict.get("category"),
        bpl=profile_dict.get("bpl"),
        aadhaar_masked=masked_aadhaar,
        bank_account_masked=masked_bank,
        yojanamatch_eligible=profile_dict.get("yojanamatch_eligible"),
        yojanamatch_score=profile_dict.get("yojanamatch_score"),
    )


class ParchaaDataService:
    """
    Deterministic data service for Parchaa Dossier compilation.
    Strictly uses verified database sources without fabricating data.
    """

    @staticmethod
    def get_scheme_by_id(scheme_id: str) -> Optional[Dict[str, Any]]:
        """
        Looks up scheme from verified database seed list.
        """
        for s in VERIFIED_SCHEMES_SEED:
            if s["id"] == scheme_id:
                return s
        return None

    @classmethod
    def assemble_scheme_summary(cls, raw_scheme: Dict[str, Any]) -> ParchaaSchemeSummary:
        """
        Extracts structured scheme summary with statutory benefits and eligibility criteria.
        """
        meta = VERIFIED_SCHEME_METADATA.get(raw_scheme["id"], {})
        
        # Build eligibility summary strings from verified rules
        eligibility_summary = []
        for r in raw_scheme.get("rules", []):
            if r.get("description"):
                eligibility_summary.append(r["description"])
            else:
                eligibility_summary.append(f"{r.get('field', '').title()} must be {r.get('operator')} {r.get('value')}")

        target = meta.get("target_beneficiaries") or f"Eligible {raw_scheme.get('occupation', 'citizens')} in {raw_scheme.get('state') or 'India'}"

        return ParchaaSchemeSummary(
            scheme_id=raw_scheme["id"],
            scheme_name=raw_scheme["name"],
            category=raw_scheme.get("category") or "General Civic Welfare",
            short_description=raw_scheme.get("short_description") or "",
            detailed_description=raw_scheme.get("detailed_description") or "",
            target_beneficiaries=target,
            main_benefits=raw_scheme.get("benefits") or [],
            eligibility_summary=eligibility_summary,
            official_source_url=raw_scheme.get("official_source_url") or "",
            application_url=raw_scheme.get("application_url"),
        )

    @classmethod
    def assemble_document_items(
        cls,
        raw_scheme: Dict[str, Any],
        document_readiness: Optional[List[ParchaaDocumentItem]] = None,
    ) -> List[ParchaaDocumentItem]:
        """
        Extracts required scheme documents and integrates readiness status (from KagazCheck).
        """
        required_doc_names = raw_scheme.get("required_documents") or []
        doc_items: List[ParchaaDocumentItem] = []

        readiness_map: Dict[str, ParchaaDocumentItem] = {}
        if document_readiness:
            for item in document_readiness:
                readiness_map[item.document_name.lower().strip()] = item
                if item.document_code:
                    readiness_map[item.document_code.lower().strip()] = item

        for doc_name in required_doc_names:
            matched_status = DocumentStatusEnum.REQUIRED
            action_needed = "Obtain document copy"
            enclosure_note = "Self-attested physical photocopy required"

            # Check if KagazCheck readiness was passed in
            for key, ready_item in readiness_map.items():
                if key in doc_name.lower() or doc_name.lower() in key:
                    matched_status = ready_item.status
                    if ready_item.action_needed:
                        action_needed = ready_item.action_needed
                    if ready_item.enclosure_note:
                        enclosure_note = ready_item.enclosure_note
                    break

            doc_items.append(
                ParchaaDocumentItem(
                    document_name=doc_name,
                    status=matched_status,
                    required=True,
                    enclosure_note=enclosure_note,
                    action_needed=action_needed,
                )
            )

        return doc_items

    @classmethod
    def assemble_application_info(
        cls,
        raw_scheme: Dict[str, Any],
        doc_items: List[ParchaaDocumentItem],
    ) -> ParchaaApplicationInfo:
        """
        Gathers verified application channel, administrative office, process steps, enclosures, and timeline.
        Strictly prevents hallucinated office addresses and processing times.
        """
        scheme_id = raw_scheme["id"]
        meta = VERIFIED_SCHEME_METADATA.get(scheme_id)

        # 1. Administrative Office
        if meta and meta.get("administrative_office"):
            off = meta["administrative_office"]
            office = ParchaaOffice(
                office_name=off.get("office_name", "Designated Nodal Office"),
                department=off.get("department", "Concerned Government Ministry"),
                address=off.get("address"),
                district=off.get("district"),
                state=raw_scheme.get("state"),
                contact_info=off.get("contact_info"),
                is_verified=True,
                unverified_notice=None,
            )
        else:
            office = ParchaaOffice(
                office_name="Local Administrative Department",
                department="Concerned Government Authority",
                address=None,
                district=None,
                state=raw_scheme.get("state"),
                contact_info=None,
                is_verified=False,
                unverified_notice="Office information not available in the current verified database.",
            )

        # 2. Processing Timeline
        if meta and meta.get("processing_timeline"):
            tl = meta["processing_timeline"]
            timeline = ParchaaTimeline(
                expected_days=tl.get("expected_days"),
                timeline_description=tl.get("timeline_description", "As per scheme operational guidelines"),
                is_verified=True,
                unverified_notice=None,
            )
        else:
            timeline = ParchaaTimeline(
                expected_days=None,
                timeline_description="Standard administrative processing window",
                is_verified=False,
                unverified_notice="Processing timeline not available in the current verified database.",
            )

        # 3. Application Channel & Portal
        app_channel = (
            meta.get("application_channel")
            if meta
            else "Official Government Portal / Village Gram Panchayat / CSC Centre"
        )

        # 4. Enclosures
        if meta and meta.get("enclosures"):
            enclosures = meta["enclosures"]
        else:
            enclosures = [f"Self-attested copy of {doc.document_name}" for doc in doc_items]

        # 5. Process Steps
        if meta and meta.get("process_steps"):
            process_steps = meta["process_steps"]
        else:
            process_steps = [
                "1. Prepare required documents and self-attested photocopies.",
                "2. Visit the official portal or nearest CSC / Gram Panchayat office.",
                "3. Fill in the statutory application form with accurate personal and bank details.",
                "4. Submit application and obtain physical or digital acknowledgment receipt.",
                "5. Track application verification status on the official portal."
            ]

        # 6. Actionable Next Step
        ready_count = sum(1 for d in doc_items if d.status in (DocumentStatusEnum.READY, DocumentStatusEnum.VERIFIED))
        total_count = len(doc_items)
        if ready_count == total_count and total_count > 0:
            next_action = "All required documents are ready. Proceed to submit your application online or at your nearest CSC / Gram Panchayat office."
        elif ready_count > 0:
            next_action = f"Next Step: {ready_count} of {total_count} documents ready. Prepare the documents marked Ready and obtain the documents marked Missing before applying."
        else:
            next_action = "Next Step: Prepare the documents marked Ready and obtain the documents marked Missing before applying."

        return ParchaaApplicationInfo(
            application_channel=app_channel,
            official_portal_url=raw_scheme.get("application_url") or raw_scheme.get("official_source_url"),
            physical_enclosures=enclosures,
            process_steps=process_steps,
            administrative_office=office,
            processing_timeline=timeline,
            next_step_action=next_action,
        )


parchaa_data_service = ParchaaDataService()
