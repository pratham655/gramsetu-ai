import os
import io
import base64
import logging
from typing import Optional
import httpx

from app.schemas.vanibot import VaniSpeakResponse
from app.services.vanibot.language_service import language_service

logger = logging.getLogger(__name__)


class VaniTextToSpeechService:
    """
    Text-to-Speech provider abstraction for Indian regional languages.
    Primary providers:
      1. gTTS (Google Text-to-Speech) - isolated backend synthesis supporting Kannada ('kn'), Hindi ('hi'), English ('en').
      2. OpenAI TTS ('tts-1') when OPENAI_API_KEY is configured.
      3. Client-side Web Speech fallback instruction when offline.
    Returns: Base64-encoded playable audio/mp3 string.
    """

    async def synthesize_speech(
        self,
        text: str,
        language: str = "kn",
        speed: float = 1.0,
    ) -> VaniSpeakResponse:
        """
        Synthesizes text into base64-encoded playable MP3 audio.
        """
        lang_code = language_service.normalize_language_code(language)
        if not text or not text.strip():
            return VaniSpeakResponse(
                language=lang_code,
                audio_base64=None,
                status="empty_text",
                provider="none",
                message="Text is empty.",
            )

        clean_text = text.replace("*", "").replace("#", "").replace("`", "").strip()
        # Truncate text to avoid excessively long audio buffers for voice UX
        if len(clean_text) > 800:
            clean_text = clean_text[:797] + "..."

        # Provider 1: gTTS (Google Text to Speech Python library)
        try:
            from gtts import gTTS
            tts_lang_map = {
                "kn": "kn",
                "hi": "hi",
                "en": "en",
                "te": "te",
                "ta": "ta",
                "mr": "mr",
            }
            target_gtts_lang = tts_lang_map.get(lang_code, "kn")
            
            mp3_fp = io.BytesIO()
            tts = gTTS(text=clean_text, lang=target_gtts_lang, slow=False)
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            
            audio_b64 = base64.b64encode(mp3_fp.read()).decode("utf-8")
            return VaniSpeakResponse(
                language=lang_code,
                audio_base64=audio_b64,
                mime_type="audio/mp3",
                status="success",
                provider="gtts",
                message="Synthesized via isolated gTTS regional engine.",
            )
        except Exception as e:
            logger.warning(f"gTTS backend synthesis exception: {e}")

        # Provider 2: OpenAI TTS API
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and len(openai_key) > 5:
            try:
                url = "https://api.openai.com/v1/audio/speech"
                headers = {
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": "tts-1",
                    "input": clean_text[:400],
                    "voice": "nova" if lang_code == "hi" else "alloy",
                    "response_format": "mp3",
                    "speed": speed,
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(url, headers=headers, json=payload)
                    if res.status_code == 200:
                        audio_b64 = base64.b64encode(res.content).decode("utf-8")
                        return VaniSpeakResponse(
                            language=lang_code,
                            audio_base64=audio_b64,
                            mime_type="audio/mp3",
                            status="success",
                            provider="openai_tts",
                            message="Synthesized via OpenAI neural TTS.",
                        )
            except Exception as e:
                logger.warning(f"OpenAI TTS provider exception: {e}")

        # Provider 3: Fallback signaling browser SpeechSynthesis
        return VaniSpeakResponse(
            language=lang_code,
            audio_base64=None,
            mime_type="audio/mp3",
            status="client_playback",
            provider="web_speech_api",
            message="Server audio synthesis offline; browser Web Speech API enabled for playback.",
        )


text_to_speech_service = VaniTextToSpeechService()
