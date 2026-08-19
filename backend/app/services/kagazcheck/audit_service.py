import re
from typing import List, Dict, Any, Optional, Tuple
from app.schemas.kagazcheck import (
    ChecklistItem,
    SchemeReadinessAudit,
    DocumentAnalysisResult,
)
from app.data.verified_schemes import VERIFIED_SCHEMES_SEED
import logging

logger = logging.getLogger(__name__)

# Canonical mapping from scheme document phrases to document type codes
DOCUMENT_KEYWORD_MAP = [
    (r"aadhaar", "aadhaar", "Aadhaar Card"),
    (r"land|ror|khasra|khatauni|ownership|homestead", "land_record", "Land Ownership Record (RoR / Khasra)"),
    (r"bank|passbook", "bank_passbook", "Bank Account Passbook"),
    (r"ration|bpl|secc", "ration_card", "Ration / BPL Card"),
    (r"residence|electricity bill|house tax|water bill|address proof|domicile", "residence_proof", "Proof of Residence / Utility Bill"),
    (r"photo|photograph", "photograph", "Passport-size Photograph"),
    (r"declaration|self-declaration|affidavit", "self_declaration", "Self-Declaration / Affidavit"),
    (r"income|aamdani", "income_certificate", "Income Certificate"),
    (r"caste|community|category", "caste_certificate", "Caste / Category Certificate"),
    (r"mgnrega|job card", "mgnrega_card", "MGNREGA Job Card"),
    (r"mcp|mother|child", "mcp_card", "Mother & Child Protection (MCP) Card"),
    (r"voter|epic", "voter_id", "Voter Identity Card (EPIC)"),
    (r"pan", "pan_card", "PAN Card"),
    (r"mobile|phone", "mobile_linked", "Aadhaar-linked Mobile Number"),
    (r"farmer identification|fid|kutumba", "fid_card", "Farmer ID / Kutumba ID"),
    (r"admission|fee receipt|student", "student_admission", "College Admission / Fee Receipt"),
]



class SchemeAuditService:
    """
    Evaluates itemized document readiness and missing requirements for specific government schemes.
    """

    @classmethod
    def match_doc_requirement_code(cls, requirement_str: str) -> Tuple[str, str]:
        """
        Maps a human-readable scheme requirement string into a canonical document code and display name.
        """
        low = requirement_str.lower()
        for pattern, code, name in DOCUMENT_KEYWORD_MAP:
            if re.search(pattern, low):
                return code, name
        return "general_document", requirement_str

    @classmethod
    def find_scheme_by_id(cls, scheme_id: str) -> Optional[Dict[str, Any]]:
        """
        Look up scheme details from seed catalog or database.
        """
        for s in VERIFIED_SCHEMES_SEED:
            if s.get("id") == scheme_id:
                return s
        return None

    @classmethod
    def audit_scheme_readiness(
        cls,
        scheme_id: str,
        analyzed_docs: List[DocumentAnalysisResult],
    ) -> SchemeReadinessAudit:
        """
        Compares uploaded analyzed documents against statutory scheme requirements.
        Generates itemized checklist and overall readiness percentage.
        """
        scheme = cls.find_scheme_by_id(scheme_id)
        if not scheme:
            # Fallback generic scheme
            scheme_name = scheme_id.replace("-", " ").title()
            required_docs = ["Aadhaar Card", "Bank Account Passbook"]
        else:
            scheme_name = scheme.get("name", scheme_id)
            required_docs = scheme.get("required_documents", [])

        # Index analyzed docs by document_type_code
        docs_by_code: Dict[str, DocumentAnalysisResult] = {}
        for d in analyzed_docs:
            code = d.document_type_code
            # Keep highest valid document if multiple of same type
            if code not in docs_by_code or d.overall_status == "VALID":
                docs_by_code[code] = d

        checklist: List[ChecklistItem] = []
        ready_count = 0
        critical_missing: List[str] = []

        for req in required_docs:
            code, name = cls.match_doc_requirement_code(req)
            
            # Special case: phone number requirement (informational)
            if code == "mobile_linked":
                checklist.append(
                    ChecklistItem(
                        document_code=code,
                        document_name=req,
                        required=True,
                        status="VALID",
                        details="Active Mobile Number linked with UIDAI Aadhaar database for OTP verification.",
                        action_needed="Ensure SMS OTP reception is active",
                    )
                )
                ready_count += 1
                continue

            matched_doc = docs_by_code.get(code)

            if matched_doc:
                if matched_doc.overall_status == "VALID":
                    status = "VALID"
                    details = f"Verified: {matched_doc.file_name} (Quality: {int(matched_doc.image_quality_score)}%)"
                    action = "Ready for official submission"
                    ready_count += 1
                elif matched_doc.overall_status == "WARNING":
                    status = "WARNING"
                    details = f"Uploaded with warnings: {', '.join(matched_doc.summary_notes) or 'Check details'}"
                    action = matched_doc.recommended_action or "Review warnings"
                    ready_count += 1  # Counted with warning
                else:
                    status = "INVALID"
                    details = f"Invalid/Unreadable: {matched_doc.file_name}"
                    action = matched_doc.recommended_action or "Re-upload a clear copy"
                    critical_missing.append(req)
                
                checklist.append(
                    ChecklistItem(
                        document_code=code,
                        document_name=req,
                        required=True,
                        status=status,
                        uploaded_document_id=matched_doc.document_id,
                        details=details,
                        action_needed=action,
                    )
                )
            else:
                checklist.append(
                    ChecklistItem(
                        document_code=code,
                        document_name=req,
                        required=True,
                        status="MISSING",
                        details="Document has not been uploaded yet.",
                        action_needed=f"Photograph or upload {req}",
                    )
                )
                critical_missing.append(req)

        total_req = len(required_docs)
        readiness_pct = round((ready_count / total_req * 100.0), 1) if total_req > 0 else 100.0
        is_ready = ready_count == total_req

        if is_ready:
            rec = f"All {total_req} required certificates verified! Your dossier is 100% ready for application submission."
        elif ready_count > 0:
            rec = f"{ready_count} of {total_req} documents ready ({int(readiness_pct)}%). Please upload the remaining {len(critical_missing)} document(s) to complete readiness."
        else:
            rec = f"Upload the {total_req} statutory documents listed below to audit eligibility readiness for {scheme_name}."

        return SchemeReadinessAudit(
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            total_required_docs=total_req,
            ready_docs_count=ready_count,
            readiness_percentage=readiness_pct,
            is_ready_to_apply=is_ready,
            checklist=checklist,
            critical_missing_docs=critical_missing,
            overall_recommendation=rec,
        )


scheme_audit_service = SchemeAuditService()
