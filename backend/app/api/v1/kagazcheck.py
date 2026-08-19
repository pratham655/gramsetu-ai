import json
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from app.schemas.kagazcheck import (
    KagazCheckAnalyzeResponse,
    DocumentTypeSpecification,
    SchemeReadinessAudit,
    BatchAuditRequest,
)
from app.services.kagazcheck.document_service import document_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kagazcheck", tags=["KagazCheck - Vision Document Auditor"])


@router.get(
    "/document-types",
    response_model=List[DocumentTypeSpecification],
    summary="List Supported Government Document Types",
    description="Returns the statutory specification and required fields for all supported Indian documents.",
)
async def get_document_types():
    return document_service.get_supported_document_types()


@router.post(
    "/analyze",
    response_model=KagazCheckAnalyzeResponse,
    summary="Analyze and Validate Uploaded Document / Camera Capture",
    description="Performs OCR extraction, deterministic field validation, citizen profile cross-matching, and scheme readiness audit.",
)
async def analyze_document(
    file: UploadFile = File(..., description="Document image or PDF captured from camera or file upload"),
    scheme_id: Optional[str] = Form(None, description="Optional government scheme ID to evaluate readiness against"),
    citizen_profile: Optional[str] = Form(None, description="Optional citizen profile JSON string for cross-matching"),
):
    # Enforce max file size: 10MB
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum allowed limit of 10MB.",
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    profile_dict = None
    if citizen_profile:
        try:
            profile_dict = json.loads(citizen_profile)
        except Exception as e:
            logger.warning(f"Could not parse citizen_profile JSON in KagazCheck: {e}")

    try:
        result = document_service.analyze_document(
            file_bytes=contents,
            file_name=file.filename or "uploaded_document",
            mime_type=file.content_type or "application/octet-stream",
            citizen_profile=profile_dict,
            scheme_id=scheme_id,
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing document in KagazCheck: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document analysis failed: {str(e)}",
        )


@router.post(
    "/audit",
    response_model=SchemeReadinessAudit,
    summary="Evaluate Overall Scheme Document Readiness",
    description="Calculates itemized readiness checklist for a given scheme across audited documents.",
)
async def audit_scheme_readiness(req: BatchAuditRequest):
    try:
        return document_service.audit_batch(
            scheme_id=req.scheme_id,
            document_ids=req.document_ids,
        )
    except Exception as e:
        logger.error(f"Error auditing scheme readiness: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scheme audit failed: {str(e)}",
        )


@router.post(
    "/session/clear",
    summary="Clear KagazCheck In-Memory Session Cache",
    description="Resets the in-memory document audit workspace for the active session.",
)
async def clear_session():
    document_service.clear_session_documents()
    return {"status": "success", "message": "KagazCheck session cache cleared."}
