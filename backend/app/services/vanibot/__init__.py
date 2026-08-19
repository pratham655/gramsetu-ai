from typing import List, Dict, Any, Optional
from app.schemas.vanibot import (
    VaniLanguageInfo,
    VaniTranscribeResponse,
    VaniSpeakResponse,
    VaniRespondRequest,
    VaniRespondResponse,
    VaniConversationTurnRequest,
    VaniConversationTurnResponse,
)
from app.services.vanibot.language_service import language_service
from app.services.vanibot.speech_to_text import speech_to_text_service
from app.services.vanibot.text_to_speech import text_to_speech_service
from app.services.vanibot.conversation_service import conversation_service


class VaniBotService:
    """
    Main orchestrator for Vani-Bot Multilingual Conversational Voice Engine.
    """

    def get_supported_languages(self) -> List[VaniLanguageInfo]:
        return language_service.get_supported_languages()

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "kn",
        mime_type: str = "audio/webm",
    ) -> VaniTranscribeResponse:
        return await speech_to_text_service.transcribe_audio(
            audio_bytes=audio_bytes,
            language=language,
            mime_type=mime_type,
        )

    async def speak(
        self,
        text: str,
        language: str = "kn",
        speed: float = 1.0,
    ) -> VaniSpeakResponse:
        return await text_to_speech_service.synthesize_speech(
            text=text,
            language=language,
            speed=speed,
        )

    async def respond(self, req: VaniRespondRequest) -> VaniRespondResponse:
        response = conversation_service.respond(req)
        if req.include_audio and response.reply_text:
            speak_res = await text_to_speech_service.synthesize_speech(
                text=response.reply_text,
                language=response.language,
            )
            response.reply_audio_base64 = speak_res.audio_base64
        return response

    async def process_conversation_turn(
        self,
        req: VaniConversationTurnRequest,
    ) -> VaniConversationTurnResponse:
        """
        Processes full multi-turn voice/text input to audio/visual response.
        """
        transcribed_text = req.text_query or ""
        detected_lang = req.language

        # If audio provided, transcribe first
        if req.audio_base64:
            import base64
            try:
                audio_bytes = base64.b64decode(req.audio_base64)
                trans_res = await speech_to_text_service.transcribe_audio(
                    audio_bytes=audio_bytes,
                    language=req.language,
                )
                if trans_res.transcript:
                    transcribed_text = trans_res.transcript
                detected_lang = trans_res.detected_language
            except Exception as e:
                pass

        respond_req = VaniRespondRequest(
            query=transcribed_text or "Hello",
            language=detected_lang,
            session_id=req.session_id,
            citizen_profile=req.citizen_profile,
            context_scheme_id=req.context_scheme_id,
            include_audio=True,
        )
        resp = await self.respond(respond_req)

        return VaniConversationTurnResponse(
            session_id=resp.session_id,
            transcribed_query=transcribed_text,
            detected_language=resp.language,
            reply_text=resp.reply_text,
            reply_audio_base64=resp.reply_audio_base64,
            scheme_cards=resp.scheme_cards,
            action_links=resp.action_links,
            sources=resp.sources,
            suggested_followups=resp.suggested_followups,
        )

    def clear_session(self, session_id: str):
        conversation_service.clear_session(session_id)


vanibot_service = VaniBotService()

__all__ = [
    "vanibot_service",
    "speech_to_text_service",
    "text_to_speech_service",
    "language_service",
    "conversation_service",
]
