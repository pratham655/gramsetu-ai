from typing import List, Dict, Any, Optional
from app.schemas.vani import (
    VaniConverseRequest,
    VaniConverseResponse,
    VaniTranscriptionResponse,
    VaniSynthesisResponse,
    VaniLanguageInfo,
)
from app.services.vani.language_service import language_service
from app.services.vani.stt_service import stt_service
from app.services.vani.tts_service import tts_service
from app.services.vani.conversation_service import conversation_service


class VaniService:
    """
    Main orchestrator for Vani-Bot Multilingual Conversational Voice Engine.
    """

    def get_supported_languages(self) -> List[VaniLanguageInfo]:
        return language_service.get_supported_languages()

    async def converse(self, req: VaniConverseRequest) -> VaniConverseResponse:
        return conversation_service.converse(req)

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "kn",
        mime_type: str = "audio/webm",
    ) -> VaniTranscriptionResponse:
        return await stt_service.transcribe_audio(
            audio_bytes=audio_bytes,
            language=language,
            mime_type=mime_type,
        )

    async def synthesize(
        self,
        text: str,
        language: str = "kn",
        speed: float = 1.0,
    ) -> VaniSynthesisResponse:
        return await tts_service.synthesize_speech(
            text=text,
            language=language,
            speed=speed,
        )

    def clear_session(self, session_id: str):
        conversation_service.clear_session(session_id)


vani_service = VaniService()
