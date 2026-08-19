from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class SupportedLanguageEnum(str, Enum):
    KANNADA = "kn"
    HINDI = "hi"
    ENGLISH = "en"
    TELUGU = "te"
    TAMIL = "ta"
    MARATHI = "mr"


class VaniSchemeCard(BaseModel):
    scheme_id: str
    scheme_name: str
    category: Optional[str] = None
    state: Optional[str] = None
    short_summary: str
    eligible_status: Optional[bool] = None
    match_score: Optional[float] = None
    key_benefits: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    official_url: str = ""
    kagazcheck_ready: bool = True


class VaniActionLink(BaseModel):
    label: str
    action_type: str  # "open_kagazcheck", "view_scheme", "check_eligibility", "open_url"
    payload: Dict[str, Any] = Field(default_factory=dict)


class VaniMessage(BaseModel):
    id: str
    sender: str  # "user" | "vani"
    text: str
    language: str = "en"
    timestamp: str
    audio_base64: Optional[str] = None
    scheme_cards: List[VaniSchemeCard] = Field(default_factory=list)
    action_links: List[VaniActionLink] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class VaniConverseRequest(BaseModel):
    user_query: str
    language: str = "kn"  # "kn" | "hi" | "en"
    session_id: Optional[str] = None
    citizen_profile: Optional[Dict[str, Any]] = None
    context_scheme_id: Optional[str] = None


class VaniConverseResponse(BaseModel):
    session_id: str
    user_query: str
    language: str
    detected_intent: str
    reply_text: str
    reply_audio_base64: Optional[str] = None
    scheme_cards: List[VaniSchemeCard] = Field(default_factory=list)
    action_links: List[VaniActionLink] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    suggested_followups: List[str] = Field(default_factory=list)


class VaniTranscriptionResponse(BaseModel):
    transcribed_text: str
    detected_language: str
    confidence: float = 1.0
    duration_seconds: Optional[float] = None


class VaniSynthesisRequest(BaseModel):
    text: str
    language: str = "kn"  # "kn" | "hi" | "en"
    speed: float = 1.0


class VaniSynthesisResponse(BaseModel):
    language: str
    audio_base64: Optional[str] = None
    mime_type: str = "audio/mp3"
    message: str = "Synthesis ready"


class VaniLanguageInfo(BaseModel):
    code: str
    locale: str
    name: str
    native_name: str
    supported_for_stt: bool = True
    supported_for_tts: bool = True
    sample_queries: List[str] = Field(default_factory=list)
