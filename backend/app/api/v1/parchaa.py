from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from app.schemas.parchaa import ParchaaRequest, ParchaaResponse
from app.services.parchaa.parchaa_service import parchaa_service

router = APIRouter(prefix="/parchaa", tags=["Parchaa Generator"])


@router.post(
    "/generate",
    response_model=ParchaaResponse,
    summary="Generate One-Click Scheme Application Parchaa",
    description="Generates a structured, deterministic single-page application dossier with embedded PDF for the citizen.",
)
def generate_parchaa_dossier(request: ParchaaRequest) -> ParchaaResponse:
    """
    Accepts scheme ID, citizen profile, and document readiness context to compile
    a verified civic-tech application dossier (Parchaa) with single-page PDF.
    """
    return parchaa_service.generate_parchaa(request)


@router.post(
    "/download",
    summary="Download Parchaa PDF Directly",
    description="Generates and streams the binary application dossier PDF directly for download or inline browser viewing.",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns raw PDF document binary.",
        }
    },
)
def download_parchaa_pdf(request: ParchaaRequest) -> Response:
    """
    Streams binary application dossier PDF with proper Content-Disposition header.
    """
    pdf_bytes = parchaa_service.generate_parchaa_pdf_bytes(request)
    filename = f"GramSetu_Parchaa_{request.scheme_id}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/pdf",
        },
    )


@router.get(
    "/preview/{scheme_id}",
    response_model=ParchaaResponse,
    summary="Get Parchaa Scheme Preview Metadata",
    description="Fetches verified scheme information and structured dossier layout for preview before generating final PDF.",
)
def get_parchaa_preview(
    scheme_id: str,
    language: Optional[str] = Query("en", description="Preferred language code: en, hi, kn"),
) -> ParchaaResponse:
    """
    Returns preview data for the given scheme ID.
    """
    return parchaa_service.get_parchaa_preview(scheme_id=scheme_id, language=language)
