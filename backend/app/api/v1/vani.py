from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from app.schemas.vani import (
    VaniConverseRequest,
    VaniConverseResponse,
    VaniTranscriptionResponse,
    VaniSynthesisRequest,
    VaniSynthesisResponse,
    VaniLanguageInfo,
)
from app.services.vani.vani_service import vani_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vani", tags=["Vani-Bot - Multilingual Conversational Voice Engine"])


@router.get(
    "/languages",
    response_model=List[VaniLanguageInfo],
    summary="Get Supported Regional Languages",
    description="Returns supported languages and locales for speech-to-text, dialogue, and text-to-speech.",
)
async def get_languages():
    return vani_service.get_supported_languages()


@router.post(
    "/converse",
    response_model=VaniConverseResponse,
    summary="Send Multilingual Voice or Text Query to Vani-Bot",
    description="Performs grounded reasoning against verified government schemes and returns localized spoken text with scheme cards.",
)
async def converse(req: VaniConverseRequest):
    try:
        return await vani_service.converse(req)
    except Exception as e:
        logger.error(f"Error in Vani-Bot conversation turn: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversation turn failed: {str(e)}",
        )


@router.post(
    "/transcribe",
    response_model=VaniTranscriptionResponse,
    summary="Transcribe Spoken Voice Audio to Text",
    description="Accepts recorded WebM/WAV voice audio and transcribes into regional text.",
)
async def transcribe_audio(
    file: UploadFile = File(..., description="Recorded audio clip from microphone"),
    language: str = Form("kn", description="Target language code (kn, hi, en)"),
):
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio recording exceeds maximum limit of 10MB.",
        )

    try:
        return await vani_service.transcribe(
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
    "/synthesize",
    response_model=VaniSynthesisResponse,
    summary="Synthesize Text into Regional Spoken Voice",
    description="Renders regional spoken voice audio response for the citizen.",
)
async def synthesize_speech(req: VaniSynthesisRequest):
    try:
        return await vani_service.synthesize(
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
    "/session/clear",
    summary="Clear Vani-Bot Multi-Turn Session",
    description="Resets the in-memory dialogue history for a session.",
)
async def clear_session(session_id: str = Form(...)):
    vani_service.clear_session(session_id)
    return {"status": "success", "message": f"Session {session_id} cleared."}
