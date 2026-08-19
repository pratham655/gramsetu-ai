from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentStatusEnum(str, Enum):
    READY = "Ready"
    VERIFIED = "Verified"
    MISSING = "Missing"
    NEEDS_ATTENTION = "Needs Attention"
    REQUIRED = "Required"


class ParchaaCitizenProfile(BaseModel):
    """
    Sanitized Citizen Profile snapshot for Parchaa Dossier.
    """
    name: Optional[str] = Field(None, description="Citizen's name if provided")
    state: Optional[str] = Field(None, description="State of residence")
    district: Optional[str] = Field(None, description="District of residence")
    occupation: Optional[str] = Field(None, description="Primary occupation")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    gender: Optional[str] = Field(None, description="Gender")
    income: Optional[float] = Field(None, ge=0, description="Annual household income (INR)")
    landholding: Optional[float] = Field(None, ge=0, description="Landholding in acres")
    category: Optional[str] = Field(None, description="Social category (e.g. General, OBC, SC, ST)")
    bpl: Optional[bool] = Field(None, description="BPL card holder status")
    aadhaar_masked: Optional[str] = Field(None, description="Masked Aadhaar (e.g. XXXX-XXXX-7058)")
    bank_account_masked: Optional[str] = Field(None, description="Masked bank account (e.g. XXXXXX1234)")
    yojanamatch_eligible: Optional[bool] = Field(None, description="Whether citizen is eligible per YojanaMatch")
    yojanamatch_score: Optional[float] = Field(None, description="Match score percentage")


class ParchaaDocumentItem(BaseModel):
    """
    Required document item with readiness status from KagazCheck or scheme checklist.
    """
    document_name: str
    document_code: Optional[str] = None
    status: DocumentStatusEnum = DocumentStatusEnum.REQUIRED
    required: bool = True
    enclosure_note: Optional[str] = None
    action_needed: Optional[str] = None


class ParchaaOffice(BaseModel):
    """
    Verified administrative office details.
    """
    office_name: str
    department: str
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    contact_info: Optional[str] = None
    is_verified: bool = False
    unverified_notice: Optional[str] = None


class ParchaaTimeline(BaseModel):
    """
    Verified scheme application processing timeline.
    """
    expected_days: Optional[int] = None
    timeline_description: str
    is_verified: bool = False
    unverified_notice: Optional[str] = None


class ParchaaSchemeSummary(BaseModel):
    """
    Verified scheme information for the dossier.
    """
    scheme_id: str
    scheme_name: str
    category: str
    short_description: str
    detailed_description: str
    target_beneficiaries: str
    main_benefits: List[str]
    eligibility_summary: List[str]
    official_source_url: str
    application_url: Optional[str] = None


class ParchaaApplicationInfo(BaseModel):
    """
    Application process steps, enclosures, and official channels.
    """
    application_channel: str
    official_portal_url: Optional[str] = None
    physical_enclosures: List[str]
    process_steps: List[str]
    administrative_office: ParchaaOffice
    processing_timeline: ParchaaTimeline
    next_step_action: str


class ParchaaRequest(BaseModel):
    """
    Request model for generating an Application Parchaa.
    """
    scheme_id: str = Field(..., description="ID of the selected government scheme")
    citizen_profile: Optional[ParchaaCitizenProfile] = None
    application_context: Optional[Dict[str, Any]] = None
    document_readiness: Optional[List[ParchaaDocumentItem]] = None
    kagazcheck_ready_count: Optional[int] = None
    kagazcheck_total_count: Optional[int] = None
    preferred_language: Optional[str] = Field("en", description="Language code: en, hi, kn")


class ParchaaResponse(BaseModel):
    """
    Complete Parchaa generation response with metadata and PDF data.
    """
    parchaa_id: str
    reference_number: str
    generated_at: str
    scheme: ParchaaSchemeSummary
    citizen: Optional[ParchaaCitizenProfile] = None
    documents: List[ParchaaDocumentItem]
    application_info: ParchaaApplicationInfo
    pdf_base64: Optional[str] = None
    pdf_filename: str
    page_count: int = 1
    language: str = "en"
