from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class EligibilityRuleBase(BaseModel):
    field: str
    operator: str
    value: str
    description: Optional[str] = None


class EligibilityRuleRead(EligibilityRuleBase):
    id: str
    scheme_id: str

    class Config:
        from_attributes = True


class SchemeBase(BaseModel):
    name: str
    short_description: str
    detailed_description: str
    benefits: List[str] = Field(default_factory=list)
    state: Optional[str] = None
    category: Optional[str] = None
    occupation: Optional[str] = None
    official_source_url: str
    application_url: Optional[str] = None
    required_documents: List[str] = Field(default_factory=list)
    active: bool = True


class SchemeRead(SchemeBase):
    id: str
    created_at: datetime
    updated_at: datetime
    rules: List[EligibilityRuleRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
