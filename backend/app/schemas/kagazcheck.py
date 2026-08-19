from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class DocumentTypeEnum(str, Enum):
    AADHAAR = "aadhaar"
    LAND_RECORD = "land_record"
    BANK_PASSBOOK = "bank_passbook"
    RATION_CARD = "ration_card"
    INCOME_CERTIFICATE = "income_certificate"
    CASTE_CERTIFICATE = "caste_certificate"
    VOTER_ID = "voter_id"
    PAN_CARD = "pan_card"
    MGNREGA_CARD = "mgnrega_card"
    MCP_CARD = "mcp_card"
    GENERAL_DOCUMENT = "general_document"
    UNKNOWN = "unknown"


class FieldValidationResult(BaseModel):
    field: str
    label: str
    extracted_value: Optional[str] = None
    is_valid: bool
    rule_description: str
    issue_reason: Optional[str] = None


class ProfileMatchItem(BaseModel):
    field: str
    profile_value: Optional[str] = None
    document_value: Optional[str] = None
    matched: bool
    confidence: float = 1.0
    details: str


class DocumentAnalysisResult(BaseModel):
    document_id: str
    file_name: str
    file_size_bytes: int = 0
    mime_type: str = "application/octet-stream"
    document_type: str
    document_type_code: str
    document_type_confidence: float = 0.0
    is_detected: bool = True
    is_readable: bool = True
    image_quality_score: float = 100.0  # 0 - 100
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    fields_validation: List[FieldValidationResult] = Field(default_factory=list)
    validity_status: str = "VALID"  # VALID, WARNING, INVALID, EXPIRED
    citizen_details_match: str = "MATCH"  # MATCH, PARTIAL_MATCH, MISMATCH, UNVERIFIED
    profile_match_details: List[ProfileMatchItem] = Field(default_factory=list)
    overall_status: str = "VALID"  # VALID, WARNING, INVALID
    summary_notes: List[str] = Field(default_factory=list)
    recommended_action: str = ""


class ChecklistItem(BaseModel):
    document_code: str
    document_name: str
    required: bool = True
    status: str = "MISSING"  # VALID, WARNING, MISSING, INVALID
    uploaded_document_id: Optional[str] = None
    details: str = "Document not yet uploaded."
    action_needed: str = "Upload document"


class SchemeReadinessAudit(BaseModel):
    scheme_id: str
    scheme_name: str
    total_required_docs: int
    ready_docs_count: int
    readiness_percentage: float
    is_ready_to_apply: bool
    checklist: List[ChecklistItem]
    critical_missing_docs: List[str] = Field(default_factory=list)
    overall_recommendation: str = ""


class DocumentTypeSpecification(BaseModel):
    code: str
    name: str
    aliases: List[str]
    required_fields: List[str]
    description: str
    validity_period_years: Optional[int] = None
    sample_hints: List[str] = Field(default_factory=list)


class KagazCheckAnalyzeResponse(BaseModel):
    document_result: DocumentAnalysisResult
    scheme_readiness: Optional[SchemeReadinessAudit] = None


class BatchAuditRequest(BaseModel):
    scheme_id: str
    document_ids: List[str] = Field(default_factory=list)
    citizen_profile: Optional[Dict[str, Any]] = None
