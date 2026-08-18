from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.eligibility import CitizenProfile, EligibilityMatchResponse
from app.services.yojanamatch import yojanamatch_service
from app.services.scheme_service import get_active_schemes

router = APIRouter(prefix="/eligibility", tags=["YojanaMatch Eligibility"])


@router.post(
    "/match",
    response_model=EligibilityMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate citizen profile against government scheme rules",
    description=(
        "Deterministic rule-based eligibility evaluation engine (YojanaMatch). "
        "Evaluates citizen attributes against statutory scheme criteria without using LLMs."
    ),
)
async def match_eligibility(
    profile: CitizenProfile,
    db: Optional[Session] = Depends(get_db),
) -> EligibilityMatchResponse:
    """
    Evaluates citizen profile against all active schemes and returns structured match results.
    """
    schemes = get_active_schemes(db)
    return yojanamatch_service.match_citizen(profile=profile, schemes=schemes)


@router.get(
    "/schemes",
    summary="List all active government schemes with eligibility rules",
    description="Returns all active schemes currently indexed in the system.",
)
async def list_active_schemes(
    db: Optional[Session] = Depends(get_db),
) -> List[dict]:
    """
    Returns list of active schemes with rules.
    """
    return get_active_schemes(db)
