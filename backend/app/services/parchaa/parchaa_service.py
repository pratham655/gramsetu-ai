import base64
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import logging

from app.schemas.parchaa import (
    ParchaaRequest,
    ParchaaResponse,
    ParchaaCitizenProfile,
)
from app.services.parchaa.data_service import (
    parchaa_data_service,
    sanitize_citizen_profile,
)
from app.services.parchaa.pdf_generator import pdf_generator

logger = logging.getLogger(__name__)


class ParchaaService:
    """
    Core orchestrator for Application Parchaa generation.
    Retrieves verified scheme data, applies citizen snapshot, merges KagazCheck readiness,
    and produces deterministic single-page PDF dossiers.
    """

    @classmethod
    def generate_parchaa(cls, request: ParchaaRequest) -> ParchaaResponse:
        """
        Generates full Parchaa response including structured metadata and base64-encoded PDF.
        """
        raw_scheme = parchaa_data_service.get_scheme_by_id(request.scheme_id)
        if not raw_scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme with ID '{request.scheme_id}' was not found in verified government database."
            )

        # 1. Assemble Scheme Summary
        scheme_summary = parchaa_data_service.assemble_scheme_summary(raw_scheme)

        # 2. Citizen Profile Snapshot
        citizen_profile: Optional[ParchaaCitizenProfile] = None
        if request.citizen_profile:
            # If passed as model, re-sanitize to ensure masking
            citizen_profile = sanitize_citizen_profile(request.citizen_profile.model_dump())
        elif request.application_context and request.application_context.get("citizen_profile"):
            citizen_profile = sanitize_citizen_profile(request.application_context["citizen_profile"])

        # 3. Document Items & Readiness Matrix
        document_items = parchaa_data_service.assemble_document_items(
            raw_scheme=raw_scheme,
            document_readiness=request.document_readiness,
        )

        # 4. Application Process, Enclosures & Administrative Channels
        application_info = parchaa_data_service.assemble_application_info(
            raw_scheme=raw_scheme,
            doc_items=document_items,
        )

        # 5. Build Metadata Identifiers
        parchaa_id = f"parchaa_{uuid.uuid4().hex[:12]}"
        scheme_short = request.scheme_id.split("-")[0].upper()
        ref_num = f"GS-PARCHAA-{scheme_short}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        gen_time = datetime.now().strftime("%d %b %Y, %I:%M %p")
        pdf_filename = f"GramSetu_Parchaa_{request.scheme_id}_{datetime.now().strftime('%Y%m%d')}.pdf"

        # 6. Construct Intermediate Response Object
        response = ParchaaResponse(
            parchaa_id=parchaa_id,
            reference_number=ref_num,
            generated_at=gen_time,
            scheme=scheme_summary,
            citizen=citizen_profile,
            documents=document_items,
            application_info=application_info,
            pdf_filename=pdf_filename,
            page_count=1,
            language=request.preferred_language or "en",
        )

        # 7. Render Single-Page A4 PDF
        try:
            pdf_bytes = pdf_generator.generate_pdf_bytes(response)
            response.pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"Error rendering Parchaa PDF: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate application dossier PDF: {str(e)}"
            )

        return response

    @classmethod
    def generate_parchaa_pdf_bytes(cls, request: ParchaaRequest) -> bytes:
        """
        Generates raw binary PDF bytes for streaming download.
        """
        response = cls.generate_parchaa(request)
        if response.pdf_base64:
            return base64.b64decode(response.pdf_base64)
        return pdf_generator.generate_pdf_bytes(response)

    @classmethod
    def get_parchaa_preview(
        cls,
        scheme_id: str,
        citizen_profile_dict: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> ParchaaResponse:
        """
        Retrieves structured preview metadata for the scheme before generating PDF.
        """
        cit_prof = sanitize_citizen_profile(citizen_profile_dict) if citizen_profile_dict else None
        req = ParchaaRequest(
            scheme_id=scheme_id,
            citizen_profile=cit_prof,
            preferred_language=language,
        )
        return cls.generate_parchaa(req)


parchaa_service = ParchaaService()
