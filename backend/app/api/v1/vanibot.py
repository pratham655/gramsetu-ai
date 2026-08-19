import logging
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status

from app.schemas.vanibot import (
    VaniLanguageInfo,
    VaniTranscribeResponse,
    VaniRespondRequest,
    VaniRespondResponse,
    VaniSpeakRequest,
    VaniSpeakResponse,
    VaniConversationTurnRequest,
    VaniConversationTurnResponse,
)
from app.services.vanibot import vanibot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vanibot", tags=["Vani-Bot - Multilingual Conversational Voice Engine"])


@router.get(
    "/languages",
    response_model=List[VaniLanguageInfo],
    summary="Get Supported Regional Languages",
    description="Returns supported Indian regional languages, locales, and localized sample queries.",
)
async def get_languages():
    return vanibot_service.get_supported_languages()


@router.post(
    "/transcribe",
    response_model=VaniTranscribeResponse,
    summary="Transcribe Spoken Voice Audio to Text",
    description="Accepts recorded WebM/WAV/MP3/OGG microphone voice audio and transcribes into regional text.",
)
async def transcribe(
    file: UploadFile = File(..., description="Recorded audio clip from citizen microphone"),
    language: str = Form("kn", description="Target language code (kn, hi, en, te, ta, mr)"),
):
    contents = await file.read()
    if len(contents) > 15 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio recording exceeds maximum limit of 15MB.",
        )

    try:
        return await vanibot_service.transcribe(
            audio_bytes=contents,
            language=language,
            mime_type=file.content_type or "audio/webm",
        )
    except Exception as e:
        logger.error(f"Audio transcription error in Vani-Bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )


@router.post(
    "/respond",
    response_model=VaniRespondResponse,
    summary="Send Multilingual Civic Query to Vani-Bot",
    description="Performs grounded reasoning against verified government schemes and returns localized response, scheme cards, and action links.",
)
async def respond(req: VaniRespondRequest):
    try:
        return await vanibot_service.respond(req)
    except Exception as e:
        logger.error(f"Error in Vani-Bot respond turn: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query response failed: {str(e)}",
        )


@router.post(
    "/speak",
    response_model=VaniSpeakResponse,
    summary="Synthesize Text into Regional Spoken Voice Audio",
    description="Renders Indian regional spoken voice audio response (MP3 base64) for the citizen.",
)
async def speak(req: VaniSpeakRequest):
    try:
        return await vanibot_service.speak(
            text=req.text,
            language=req.language,
            speed=req.speed,
        )
    except Exception as e:
        logger.error(f"Speech synthesis error in Vani-Bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {str(e)}",
        )


@router.post(
    "/conversation",
    response_model=VaniConversationTurnResponse,
    summary="Unified Conversational Voice Turn",
    description="Processes single-turn audio or text input to synthesized voice audio, cards, and grounded text answer.",
)
async def conversation(req: VaniConversationTurnRequest):
    try:
        return await vanibot_service.process_conversation_turn(req)
    except Exception as e:
        logger.error(f"Error in Vani-Bot conversation turn: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation turn failed: {str(e)}",
        )


@router.post(
    "/session/clear",
    summary="Clear Vani-Bot Multi-Turn Session",
    description="Resets the in-memory dialogue history and scheme context for a given session.",
)
async def clear_session(session_id: str = Form(...)):
    vanibot_service.clear_session(session_id)
    return {"status": "success", "message": f"Session {session_id} memory cleared."}
