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
    action_type: str  # "open_kagazcheck" | "view_scheme" | "check_eligibility" | "open_url"
    payload: Dict[str, Any] = Field(default_factory=dict)


class VaniLanguageInfo(BaseModel):
    code: str
    locale: str
    name: str
    native_name: str
    supported_for_stt: bool = True
    supported_for_tts: bool = True
    sample_queries: List[str] = Field(default_factory=list)


# 1. Speech to Text Schemas
class VaniTranscribeResponse(BaseModel):
    transcript: str
    detected_language: str
    confidence: float = 1.0
    status: str = "success"
    duration_seconds: Optional[float] = None
    provider: str = "default"
    error_message: Optional[str] = None


# 2. Text to Speech Schemas
class VaniSpeakRequest(BaseModel):
    text: str
    language: str = "kn"  # "kn" | "hi" | "en"
    speed: float = 1.0


class VaniSpeakResponse(BaseModel):
    language: str
    audio_base64: Optional[str] = None
    mime_type: str = "audio/mp3"
    status: str = "success"
    provider: str = "gtts"
    message: str = "Speech synthesis complete"


# 3. Conversational Query / Response Schemas
class VaniRespondRequest(BaseModel):
    query: str
    language: str = "kn"  # "kn" | "hi" | "en"
    session_id: Optional[str] = None
    citizen_profile: Optional[Dict[str, Any]] = None
    context_scheme_id: Optional[str] = None
    include_audio: bool = True


class VaniRespondResponse(BaseModel):
    session_id: str
    query: str
    language: str
    intent: str
    reply_text: str
    reply_audio_base64: Optional[str] = None
    scheme_cards: List[VaniSchemeCard] = Field(default_factory=list)
    action_links: List[VaniActionLink] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    suggested_followups: List[str] = Field(default_factory=list)
    context_scheme_id: Optional[str] = None


# 4. Multi-Turn Full Conversation Turn (Audio + Text in one payload)
class VaniConversationTurnRequest(BaseModel):
    session_id: Optional[str] = None
    language: str = "kn"
    text_query: Optional[str] = None
    audio_base64: Optional[str] = None
    citizen_profile: Optional[Dict[str, Any]] = None
    context_scheme_id: Optional[str] = None


class VaniConversationTurnResponse(BaseModel):
    session_id: str
    transcribed_query: str
    detected_language: str
    reply_text: str
    reply_audio_base64: Optional[str] = None
    scheme_cards: List[VaniSchemeCard] = Field(default_factory=list)
    action_links: List[VaniActionLink] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    suggested_followups: List[str] = Field(default_factory=list)
