import asyncio
from app.schemas.vanibot import (
    VaniRespondRequest,
    VaniSpeakRequest,
    VaniConversationTurnRequest,
)

from app.services.vanibot.language_service import language_service
from app.services.vanibot.speech_to_text import speech_to_text_service
from app.services.vanibot.text_to_speech import text_to_speech_service
from app.services.vanibot.conversation_service import conversation_service
from app.services.vanibot import vanibot_service
from app.schemas.eligibility import CitizenProfile
import asyncio


# Test 1: Supported Languages and Normalization
def test_supported_languages_and_normalization():
    languages = language_service.get_supported_languages()
    lang_codes = [l.code for l in languages]
    assert "kn" in lang_codes
    assert "hi" in lang_codes
    assert "en" in lang_codes
    assert "te" in lang_codes

    # Normalization tests
    assert language_service.normalize_language_code("kn-IN") == "kn"
    assert language_service.normalize_language_code("hi_IN") == "hi"
    assert language_service.normalize_language_code("en-US") == "en"
    # Invalid / None language should default safely to "kn"
    assert language_service.normalize_language_code(None) == "kn"
    assert language_service.normalize_language_code("invalid_lang_xyz") == "kn"


# Test 2: Speech to Text Request Validation & Fallback
def test_stt_transcription_validation():
    # Empty audio
    res_empty = asyncio.run(speech_to_text_service.transcribe_audio(b"", language="kn"))
    assert res_empty.status == "empty_audio"
    assert res_empty.confidence == 0.0

    # Non-empty mock sample audio
    sample_bytes = b"MOCK_WAV_HEADER_DATA_STREAM_FOR_TESTING_1234567890" * 10
    res = asyncio.run(speech_to_text_service.transcribe_audio(sample_bytes, language="kn"))
    assert res.transcript != ""
    assert res.detected_language == "kn"
    assert res.status in ("success", "fallback")
    assert res.provider != ""


# Test 3: Text to Speech Synthesis with gTTS / Fallback
def test_tts_synthesis():
    # Empty text
    empty_res = asyncio.run(text_to_speech_service.synthesize_speech("", language="kn"))
    assert empty_res.status == "empty_text"

    # Synthesis for Kannada
    kn_res = asyncio.run(
        text_to_speech_service.synthesize_speech(
            "ಗ್ರಾಮಸೇತು AI ಗೆ ಸ್ವಾಗತ", language="kn"
        )
    )
    assert kn_res.language == "kn"
    assert kn_res.status in ("success", "client_playback")
    if kn_res.audio_base64:
        assert len(kn_res.audio_base64) > 50
        assert kn_res.mime_type == "audio/mp3"

    # Synthesis for Hindi
    hi_res = asyncio.run(
        text_to_speech_service.synthesize_speech(
            "पीएम किसान सम्मान निधि", language="hi"
        )
    )
    assert hi_res.language == "hi"
    assert hi_res.status in ("success", "client_playback")

    # Synthesis for English
    en_res = asyncio.run(
        text_to_speech_service.synthesize_speech(
            "Welcome to GramSetu AI", language="en"
        )
    )
    assert en_res.language == "en"
    assert en_res.status in ("success", "client_playback")


# Test 4: Grounded Civic Response for Specific Schemes (PM-KISAN, PMAY-G)
def test_civic_scheme_grounded_response():
    # PM-KISAN in English
    req = VaniRespondRequest(
        query="What documents do I need for PM-KISAN?",
        language="en",
        session_id="test_sess_001",
    )
    resp = conversation_service.respond(req)
    assert resp.session_id == "test_sess_001"
    assert "PM-KISAN" in resp.reply_text or "Pradhan Mantri" in resp.reply_text
    assert len(resp.scheme_cards) >= 1
    assert resp.scheme_cards[0].scheme_id == "pm-kisan-001"
    assert any("Aadhaar" in doc for doc in resp.scheme_cards[0].required_documents)
    assert len(resp.action_links) >= 1
    assert any(a.action_type == "open_kagazcheck" for a in resp.action_links)

    # PM-KISAN in Kannada
    req_kn = VaniRespondRequest(
        query="ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
        language="kn",
        session_id="test_sess_002",
    )
    resp_kn = conversation_service.respond(req_kn)
    assert "ದಾಖಲೆಗಳು" in resp_kn.reply_text or "ಕಿಸಾನ್" in resp_kn.reply_text
    assert len(resp_kn.scheme_cards) >= 1
    assert resp_kn.scheme_cards[0].scheme_id == "pm-kisan-001"


# Test 5: Multi-Turn Conversation Context Retention
def test_multi_turn_context_resolution():
    session_id = "multi_turn_test_session"
    conversation_service.clear_session(session_id)

    # Turn 1: User asks about PM-KISAN
    turn1_req = VaniRespondRequest(
        query="Tell me about PM-KISAN scheme",
        language="en",
        session_id=session_id,
    )
    turn1_resp = conversation_service.respond(turn1_req)
    assert turn1_resp.context_scheme_id == "pm-kisan-001"
    assert len(turn1_resp.scheme_cards) > 0

    # Turn 2: User asks follow-up: "What documents do I need?" (pronoun / omitted subject)
    turn2_req = VaniRespondRequest(
        query="What documents do I need?",
        language="en",
        session_id=session_id,
    )
    turn2_resp = conversation_service.respond(turn2_req)
    # The engine should understand from session context that the user is asking about PM-KISAN
    assert turn2_resp.context_scheme_id == "pm-kisan-001"
    assert "PM-KISAN" in turn2_resp.reply_text or "Pradhan Mantri" in turn2_resp.reply_text
    assert len(turn2_resp.scheme_cards) == 1
    assert turn2_resp.scheme_cards[0].scheme_id == "pm-kisan-001"


# Test 6: Privacy Protection and PII Redaction
def test_pii_redaction():
    # Query containing a 12-digit Aadhaar number
    query_with_aadhaar = "My Aadhaar is 9999 4105 7058, can I get PM-KISAN?"
    req = VaniRespondRequest(
        query=query_with_aadhaar,
        language="en",
        session_id="pii_test_session",
    )
    resp = conversation_service.respond(req)
    # The recorded query in response must be masked
    assert "9999 4105 7058" not in resp.query
    assert "XXXX-XXXX-7058" in resp.query


# Test 7: Unified Full Turn Async Service
def test_unified_conversation_turn():
    req = VaniConversationTurnRequest(
        language="hi",
        text_query="आयुष्मान भारत योजना के क्या लाभ हैं?",
        citizen_profile={"age": 35, "bpl": True},
    )
    resp = asyncio.run(vanibot_service.process_conversation_turn(req))
    assert resp.transcribed_query == "आयुष्मान भारत योजना के क्या लाभ हैं?"
    assert resp.detected_language == "hi"
    assert len(resp.scheme_cards) >= 1
    assert "5,00,000" in resp.reply_text or "Ayushman" in resp.reply_text or "लाभ" in resp.reply_text



# Test 8: Session Clear
def test_session_clear():
    session_id = "sess_to_clear"
    req = VaniRespondRequest(
        query="What is PMAY-G?",
        language="en",
        session_id=session_id,
    )
    conversation_service.respond(req)
    assert session_id in conversation_service._session_history

    conversation_service.clear_session(session_id)
    assert session_id not in conversation_service._session_history
    assert session_id not in conversation_service._session_scheme_context


if __name__ == "__main__":
    test_supported_languages_and_normalization()
    test_stt_transcription_validation()
    test_tts_synthesis()
    test_civic_scheme_grounded_response()
    test_multi_turn_context_resolution()
    test_pii_redaction()
    test_unified_conversation_turn()
    test_session_clear()
    print("All Vani-Bot voice engine tests passed successfully!")
