import uuid
from typing import Dict, Any, List, Optional
from app.schemas.kagazcheck import (
    DocumentAnalysisResult,
    DocumentTypeSpecification,
    SchemeReadinessAudit,
    KagazCheckAnalyzeResponse,
)
from app.services.kagazcheck.ocr_service import ocr_service
from app.services.kagazcheck.validation_service import validation_engine
from app.services.kagazcheck.audit_service import scheme_audit_service
import logging

logger = logging.getLogger(__name__)

# Standard document type catalog specifications
DOCUMENT_CATALOG: List[DocumentTypeSpecification] = [
    DocumentTypeSpecification(
        code="aadhaar",
        name="Aadhaar Card",
        aliases=["Aadhaar", "UIDAI", "e-Aadhaar"],
        required_fields=["12-digit UID (Verhoeff Checksum)", "Cardholder Name", "Date/Year of Birth", "Gender"],
        description="Official proof of identity and biometric identity issued by UIDAI.",
        sample_hints=["Hold flat against a neutral surface", "Ensure all 12 digits and QR code are visible"],
    ),
    DocumentTypeSpecification(
        code="land_record",
        name="Land Record (RoR / Khasra / Khatauni)",
        aliases=["ROR", "RTC", "Pahani", "Khasra", "Khatauni", "Patta", "Bhoomi Record"],
        required_fields=["Survey / Khata / Khasra Number", "Land Extent (Acres/Guntas)", "Pattedar / Owner Name", "Revenue Authority Seal"],
        description="Official record of rights and land title issued by State Revenue Department.",
        sample_hints=["Ensure Survey Number and Land Extent table are clearly in frame"],
    ),
    DocumentTypeSpecification(
        code="bank_passbook",
        name="Bank Passbook / Statement",
        aliases=["Passbook", "Bank Account Proof", "Cancelled Cheque"],
        required_fields=["11-character RBI IFSC Code", "Account Number", "Account Holder Name", "Bank / Branch Name"],
        description="Aadhaar-seeded operational bank account passbook for Direct Benefit Transfer (DBT).",
        sample_hints=["Capture first page showing IFSC, Account Number and Bank Seal"],
    ),
    DocumentTypeSpecification(
        code="ration_card",
        name="Ration Card / BPL Proof",
        aliases=["Ration Card", "BPL Card", "NFSA Card", "Antyodaya AAY Card", "SECC Document"],
        required_fields=["Ration Card Number / NFSA ID", "Entitlement Category (BPL/AAY/PHH)", "Head of Family Name"],
        description="Food security and subsidized entitlement ration card issued by Civil Supplies.",
        sample_hints=["Ensure Category (BPL/Antyodaya) and Family Head name are visible"],
    ),
    DocumentTypeSpecification(
        code="income_certificate",
        name="Income Certificate",
        aliases=["Income Certificate", "Aaya Pramana", "Aamdani Praman Patra"],
        required_fields=["Certificate Number", "Certified Annual Household Income", "Validity Period / Expiry Date", "Tahsildar / Officer Seal"],
        description="Statutory revenue certificate certifying annual family income.",
        validity_period_years=1,
        sample_hints=["Ensure valid until date and certified income figure are readable"],
    ),
    DocumentTypeSpecification(
        code="caste_certificate",
        name="Caste / Category Certificate",
        aliases=["Caste Certificate", "Community Certificate", "Jaati Praman Patra"],
        required_fields=["Certificate Number", "Caste / Category (SC/ST/OBC)", "Applicant Name", "Issuing Authority"],
        description="Statutory reservation certificate for SC, ST, OBC and EWS categories.",
        sample_hints=["Ensure category class and certificate number are visible"],
    ),
    DocumentTypeSpecification(
        code="pan_card",
        name="PAN Card",
        aliases=["PAN", "Permanent Account Number"],
        required_fields=["10-character PAN", "Cardholder Name", "Father Name", "Date of Birth"],
        description="Permanent Account Number card issued by Income Tax Department.",
        sample_hints=["Capture front side of physical or e-PAN"],
    ),
    DocumentTypeSpecification(
        code="mgnrega_card",
        name="MGNREGA Job Card",
        aliases=["MGNREGA Card", "NREGA Job Card", "Rozgar Card"],
        required_fields=["Job Card Number", "Gram Panchayat Name", "Beneficiary Household Details"],
        description="Guaranteed rural employment entitlement card.",
        sample_hints=["Ensure Job Card registration ID is legible"],
    ),
]


class DocumentService:
    """
    Orchestration service for KagazCheck Multimodal Document Auditor.
    """

    def __init__(self):
        # In-memory document session store for prototype (keyed by doc_id)
        # Note: Only stores metadata and validation results; does not retain raw image blobs permanently.
        self._document_results_cache: Dict[str, DocumentAnalysisResult] = {}

    def get_supported_document_types(self) -> List[DocumentTypeSpecification]:
        return DOCUMENT_CATALOG

    def analyze_document(
        self,
        file_bytes: bytes,
        file_name: str,
        mime_type: str,
        citizen_profile: Optional[Dict[str, Any]] = None,
        scheme_id: Optional[str] = None,
    ) -> KagazCheckAnalyzeResponse:
        """
        Runs complete OCR extraction, deterministic field validation,
        citizen profile cross-matching, and optional scheme readiness audit.
        """
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        
        # 1. OCR & Structural Extraction
        extraction = ocr_service.extract_document_data(file_bytes, file_name, mime_type)
        
        detected_type = extraction["detected_type"]
        confidence = extraction["confidence"]
        is_readable = extraction["is_readable"]
        quality_score = extraction["quality_score"]
        extracted_fields = extraction["extracted_fields"]
        
        # Find display title
        catalog_item = next((c for c in DOCUMENT_CATALOG if c.code == detected_type), None)
        type_display_name = catalog_item.name if catalog_item else detected_type.replace("_", " ").title()

        # 2. Deterministic Field Validation
        fields_val, validity_status = validation_engine.validate_fields(
            doc_type=detected_type,
            extracted_fields=extracted_fields,
            is_readable=is_readable,
        )

        # 3. Citizen Profile Cross-Matching
        profile_match_status, profile_match_details = validation_engine.cross_match_citizen_profile(
            extracted_fields=extracted_fields,
            citizen_profile=citizen_profile,
        )

        # 4. Overall Status Determination
        summary_notes: List[str] = []
        if not is_readable:
            overall_status = "INVALID"
            summary_notes.append("Document image quality is too low or unreadable.")
            recommended_action = "Please upload or photograph a clearer, well-lit copy."
        elif validity_status == "INVALID":
            overall_status = "INVALID"
            summary_notes.append("Statutory fields or checksum validation failed.")
            recommended_action = "Please verify that the document is authentic and contains all required numbers."
        elif validity_status == "EXPIRED":
            overall_status = "INVALID"
            summary_notes.append("Certificate has passed its statutory expiry date.")
            recommended_action = "Please renew certificate at Gram Panchayat / CSC Kendra."
        elif profile_match_status == "MISMATCH":
            overall_status = "WARNING"
            summary_notes.append("Document details show discrepancy with citizen profile.")
            recommended_action = "Confirm name/state details match the applicant's official records."
        elif validity_status == "WARNING" or profile_match_status == "PARTIAL_MATCH":
            overall_status = "WARNING"
            summary_notes.append("Document accepted with minor warnings.")
            recommended_action = "Review highlighted fields before final submission."
        else:
            overall_status = "VALID"
            summary_notes.append("Document passed all deterministic statutory checks.")
            recommended_action = "Document is verified and ready for application filing."

        # Assemble Document Result
        doc_result = DocumentAnalysisResult(
            document_id=doc_id,
            file_name=file_name,
            file_size_bytes=len(file_bytes),
            mime_type=mime_type,
            document_type=type_display_name,
            document_type_code=detected_type,
            document_type_confidence=confidence,
            is_detected=detected_type != "general_document",
            is_readable=is_readable,
            image_quality_score=quality_score,
            extracted_fields=extracted_fields,
            fields_validation=fields_val,
            validity_status=validity_status,
            citizen_details_match=profile_match_status,
            profile_match_details=profile_match_details,
            overall_status=overall_status,
            summary_notes=summary_notes,
            recommended_action=recommended_action,
        )

        # Cache document result for multi-document readiness
        self._document_results_cache[doc_id] = doc_result

        # 5. Scheme Readiness Audit (if scheme_id provided)
        scheme_readiness: Optional[SchemeReadinessAudit] = None
        if scheme_id:
            all_current_docs = list(self._document_results_cache.values())
            scheme_readiness = scheme_audit_service.audit_scheme_readiness(
                scheme_id=scheme_id,
                analyzed_docs=all_current_docs,
            )

        return KagazCheckAnalyzeResponse(
            document_result=doc_result,
            scheme_readiness=scheme_readiness,
        )

    def audit_batch(
        self,
        scheme_id: str,
        document_ids: Optional[List[str]] = None,
    ) -> SchemeReadinessAudit:
        """
        Generates scheme readiness audit across previously analyzed documents.
        """
        if document_ids:
            docs = [self._document_results_cache[d] for d in document_ids if d in self._document_results_cache]
        else:
            docs = list(self._document_results_cache.values())

        return scheme_audit_service.audit_scheme_readiness(
            scheme_id=scheme_id,
            analyzed_docs=docs,
        )

    def clear_session_documents(self):
        """
        Clears temporary session cache.
        """
        self._document_results_cache.clear()


document_service = DocumentService()
