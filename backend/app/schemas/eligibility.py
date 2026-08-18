from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class CitizenProfile(BaseModel):
    """
    Structured citizen profile input for YojanaMatch eligibility evaluation.
    """
    age: Optional[int] = Field(None, ge=0, le=120, description="Age of the citizen in years")
    income: Optional[float] = Field(None, ge=0, description="Annual household income in INR")
    state: Optional[str] = Field(None, description="State of residence (e.g. Karnataka, Uttar Pradesh)")
    district: Optional[str] = Field(None, description="District of residence (e.g. Tumakuru, Varanasi)")
    gender: Optional[str] = Field(None, description="Gender (e.g. female, male, other)")
    occupation: Optional[str] = Field(None, description="Primary occupation (e.g. farmer, artisan, student, unemployed)")
    landholding: Optional[float] = Field(None, ge=0, description="Agricultural landholding in acres")
    category: Optional[str] = Field(None, description="Social category (e.g. General, OBC, SC, ST)")
    bpl: Optional[bool] = Field(None, description="Whether the citizen holds a Below Poverty Line (BPL) card")

    class Config:
        json_schema_extra = {
            "example": {
                "age": 42,
                "income": 180000,
                "state": "Karnataka",
                "district": "Tumakuru",
                "gender": "male",
                "occupation": "farmer",
                "landholding": 2.5,
                "category": "OBC",
                "bpl": True,
            }
        }


class RuleEvaluationResult(BaseModel):
    """
    Detailed explanation of a single rule evaluation.
    """
    field: str
    operator: str
    expected_value: Any
    actual_value: Any
    passed: bool
    description: Optional[str] = None


class SchemeMatchResult(BaseModel):
    """
    Evaluated result for a single scheme against a citizen profile.
    """
    scheme_id: str
    scheme_name: str
    short_description: Optional[str] = None
    detailed_description: Optional[str] = None
    match_score: float = Field(..., description="Calculated match percentage (0 to 100)")
    eligible_status: bool = Field(..., description="True if all deterministic eligibility criteria passed")
    matched_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    failed_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    benefits: Union[List[str], str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    official_source_url: str
    application_url: Optional[str] = None


class EligibilityMatchResponse(BaseModel):
    """
    API response for POST /api/v1/eligibility/match
    """
    citizen_profile: CitizenProfile
    total_schemes_evaluated: int
    eligible_schemes_count: int
    results: List[SchemeMatchResult]
