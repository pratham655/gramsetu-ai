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


# Test 9: Ration Card Intent Detection Across Variations
def test_ration_card_intent_detection():
    variations = [
        "I want to apply for ration card",
        "ration card application",
        "ration card apply",
        "how to get bpl card",
        "ration card details",
        "ರೇಷನ್ ಕಾರ್ಡ್ ಅರ್ಜಿ",
        "ಪಡಿತರ ಚೀಟಿ",
        "राशन कार्ड कैसे बनवाएं",
        "बीपीएल राशन कार्ड",
    ]
    for q in variations:
        scheme_id, conf = language_service.detect_scheme_intent(q)
        assert scheme_id == "ration-card-006", f"Failed for query: '{q}' (got {scheme_id})"
        assert conf >= 0.90


# Test 10: Multi-Turn Conversation - Exact User Scenario (Turn 1: apply for ration card, Turn 2: sure could u provide the details)
def test_ration_card_exact_conversation_flow():
    session_id = "ration_card_exact_session"
    conversation_service.clear_session(session_id)

    # Turn 1
    req1 = VaniRespondRequest(
        query="I want to apply for ration card",
        language="en",
        session_id=session_id,
        citizen_profile={"occupation": "farmer", "state": "Karnataka", "landholding": 2.5},
    )
    resp1 = conversation_service.respond(req1)
    assert resp1.context_scheme_id == "ration-card-006"
    assert "Ration Card" in resp1.reply_text or "NFSA" in resp1.reply_text
    assert len(resp1.scheme_cards) == 1
    assert resp1.scheme_cards[0].scheme_id == "ration-card-006"
    assert "Based on your current profile (farmer" not in resp1.reply_text

    # Turn 2: "sure could u provide the details"
    req2 = VaniRespondRequest(
        query="sure could u provide the details",
        language="en",
        session_id=session_id,
        citizen_profile={"occupation": "farmer", "state": "Karnataka", "landholding": 2.5},
    )
    resp2 = conversation_service.respond(req2)
    # MUST resolve context to ration-card-006
    assert resp2.context_scheme_id == "ration-card-006"
    # MUST contain actual verified ration card details
    assert "Ration Card" in resp2.reply_text or "NFSA" in resp2.reply_text
    assert "Required Documents" in resp2.reply_text or "Aadhaar" in resp2.reply_text
    # MUST NOT repeat generic redirect
    assert "view exact criteria breakdowns on the Find Schemes page" not in resp2.reply_text
    assert len(resp2.scheme_cards) == 1
    assert resp2.scheme_cards[0].scheme_id == "ration-card-006"


# Test 11: Multi-Turn Follow-Ups (Documents, Application Channels, Timeline)
def test_ration_card_sub_intent_followups():
    session_id = "ration_card_sub_intents"
    conversation_service.clear_session(session_id)

    # Initial turn
    conversation_service.respond(VaniRespondRequest(
        query="I want to apply for ration card",
        language="en",
        session_id=session_id,
    ))

    # Follow-up 1: Documents
    doc_resp = conversation_service.respond(VaniRespondRequest(
        query="What documents do I need?",
        language="en",
        session_id=session_id,
    ))
    assert doc_resp.context_scheme_id == "ration-card-006"
    assert "Aadhaar" in doc_resp.reply_text
    assert "KagazCheck" in doc_resp.reply_text
    assert doc_resp.intent == "document_inquiry"

    # Follow-up 2: Where to apply / Process
    apply_resp = conversation_service.respond(VaniRespondRequest(
        query="Where can I apply?",
        language="en",
        session_id=session_id,
    ))
    assert apply_resp.context_scheme_id == "ration-card-006"
    assert "ahara.kar.nic.in" in apply_resp.reply_text or "Gram One" in apply_resp.reply_text or "CSC" in apply_resp.reply_text
    assert apply_resp.intent == "application_guidance"

    # Follow-up 3: Processing Timeline
    time_resp = conversation_service.respond(VaniRespondRequest(
        query="How long does it take?",
        language="en",
        session_id=session_id,
    ))
    assert time_resp.context_scheme_id == "ration-card-006"
    assert "30" in time_resp.reply_text
    assert time_resp.intent == "timeline_inquiry"


# Test 12: Multilingual Continuity (Kannada & Hindi)
def test_ration_card_multilingual_continuity():
    # Kannada
    kn_sess = "kn_ration_sess"
    conversation_service.clear_session(kn_sess)
    kn_resp1 = conversation_service.respond(VaniRespondRequest(
        query="ರೇಷನ್ ಕಾರ್ಡ್ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?",
        language="kn",
        session_id=kn_sess,
    ))
    assert kn_resp1.language == "kn"
    assert kn_resp1.context_scheme_id == "ration-card-006"
    assert "ರೇಷನ್ ಕಾರ್ಡ್" in kn_resp1.reply_text or "ಪಡಿತರ" in kn_resp1.reply_text

    kn_resp2 = conversation_service.respond(VaniRespondRequest(
        query="ದಾಖಲೆಗಳು ಯಾವುವು?",
        language="kn",
        session_id=kn_sess,
    ))
    assert kn_resp2.language == "kn"
    assert kn_resp2.context_scheme_id == "ration-card-006"
    assert "ದಾಖಲೆಗಳು" in kn_resp2.reply_text or "ಆಧಾರ್" in kn_resp2.reply_text

    # Hindi
    hi_sess = "hi_ration_sess"
    conversation_service.clear_session(hi_sess)
    hi_resp1 = conversation_service.respond(VaniRespondRequest(
        query="राशन कार्ड के लिए आवेदन कैसे करें?",
        language="hi",
        session_id=hi_sess,
    ))
    assert hi_resp1.language == "hi"
    assert hi_resp1.context_scheme_id == "ration-card-006"
    assert "राशन कार्ड" in hi_resp1.reply_text

    hi_resp2 = conversation_service.respond(VaniRespondRequest(
        query="क्या दस्तावेज चाहिए?",
        language="hi",
        session_id=hi_sess,
    ))
    assert hi_resp2.language == "hi"
    assert hi_resp2.context_scheme_id == "ration-card-006"
    assert "दस्तावेज" in hi_resp2.reply_text or "आधार" in hi_resp2.reply_text


# Test 13: Unverified Missing Timeline Fallback
def test_unverified_timeline_handling():
    from app.data.verified_schemes import VERIFIED_SCHEMES_SEED

    mock_scheme = {
        "id": "mock-grant-999",
        "name": "Mock Agricultural Relief Scheme",
        "aliases": ["mock relief", "mock grant scheme"],
        "short_description": "Mock scheme without verified statutory timeline in database",
        "benefits": ["Relief grant"],
        "state": None,
        "category": "Agriculture",
        "occupation": None,
        "official_source_url": "https://example.gov.in",
        "required_documents": ["Aadhaar Card"],
        "active": True,
        "rules": []
    }
    VERIFIED_SCHEMES_SEED.append(mock_scheme)
    try:
        session_id = "mock_timeline_sess"
        conversation_service.clear_session(session_id)

        # Ask about mock scheme
        conversation_service.respond(VaniRespondRequest(
            query="Tell me about mock relief scheme",
            language="en",
            session_id=session_id,
        ))

        # Ask timeline for scheme without verified statutory timeline in database
        time_resp = conversation_service.respond(VaniRespondRequest(
            query="How many days does it take?",
            language="en",
            session_id=session_id,
        ))
        assert "not available in the current verified GramSetu database" in time_resp.reply_text
    finally:
        VERIFIED_SCHEMES_SEED.remove(mock_scheme)



# Test 14: Multiple Unrelated Schemes Verification (PMAY-G, PMMVY, PM-JAY, Raitha Vidya Nidhi, PM-KISAN)
def test_multiple_unrelated_schemes_grounded_responses():
    unrelated_test_cases = [
        {
            "query": "Tell me about PMAY-G housing grant",
            "expected_scheme_id": "pmay-g-002",
            "expected_kw": "1,20,000",
            "sub_intent": "details",
        },
        {
            "query": "How much maternity benefit under Matru Vandana Yojana?",
            "expected_scheme_id": "pmmvy-003",
            "expected_kw": "5,000",
            "sub_intent": "benefits",
        },
        {
            "query": "What health insurance does Ayushman Bharat PM-JAY offer?",
            "expected_scheme_id": "pm-jay-004",
            "expected_kw": "5,00,000",
            "sub_intent": "benefits",
        },
        {
            "query": "Karnataka farmer children scholarship Raitha Vidya Nidhi application",
            "expected_scheme_id": "raitha-vidya-005",
            "expected_kw": "ssp.postmatric.karnataka.gov.in",
            "sub_intent": "application",
        },
        {
            "query": "What are the required documents for PM-KISAN?",
            "expected_scheme_id": "pm-kisan-001",
            "expected_kw": "Aadhaar Card",
            "sub_intent": "documents",
        },
    ]

    for tc in unrelated_test_cases:
        session_id = f"test_unrelated_{tc['expected_scheme_id']}"
        conversation_service.clear_session(session_id)

        scheme_id, conf = language_service.detect_scheme_intent(tc["query"])
        assert scheme_id == tc["expected_scheme_id"], f"Failed intent for: {tc['query']} (got {scheme_id})"
        assert conf >= 0.90

        resp = conversation_service.respond(VaniRespondRequest(
            query=tc["query"],
            language="en",
            session_id=session_id,
        ))
        assert resp.context_scheme_id == tc["expected_scheme_id"]
        assert len(resp.scheme_cards) >= 1
        assert resp.scheme_cards[0].scheme_id == tc["expected_scheme_id"]
        assert tc["expected_kw"] in resp.reply_text or any(tc["expected_kw"] in b for b in resp.scheme_cards[0].key_benefits) or any(tc["expected_kw"] in d for d in resp.scheme_cards[0].required_documents) or tc["expected_kw"] in resp.scheme_cards[0].official_url


# Test 15: Dynamic Extensibility - Adding New Scheme at Runtime Without Code Changes
def test_dynamic_extensibility_with_new_scheme():
    from app.data.verified_schemes import VERIFIED_SCHEMES_SEED

    # Create a completely new custom scheme object
    custom_scheme = {
        "id": "pm-surya-ghar-007",
        "name": "PM Surya Ghar: Muft Bijli Yojana",
        "localized_names": {
            "kn": "ಪಿಎಂ ಸೂರ್ಯ ಘರ್: ಉಚಿತ ವಿದ್ಯುತ್ ಯೋಜನೆ",
            "hi": "पीएम सूर्य घर: मुफ्त बिजली योजना",
            "en": "PM Surya Ghar: Free Electricity Scheme",
        },
        "aliases": [
            "pm surya ghar", "surya ghar", "rooftop solar", "solar subsidy", "free electricity solar",
            "ಸೂರ್ಯ ಘರ್", "ಸೌರ ಶಕ್ತಿ ಯೋಜನೆ", "ಉಚಿತ ವಿದ್ಯುತ್ ಸೋಲಾರ್",
            "सूर्य घर", "सोलर योजना", "मुफ्त बिजली सोलर"
        ],
        "short_description": "Central rooftop solar subsidy scheme providing up to 300 units free electricity per month.",
        "detailed_description": "PM Surya Ghar provides substantial capital subsidy for residential rooftop solar panel installation.",
        "benefits": [
            "Subsidy of ₹30,000 to ₹78,000 for 1kW to 3kW rooftop solar installations",
            "Up to 300 units of free electricity per month for eligible households"
        ],
        "state": None,
        "category": "Renewable Energy & Power",
        "occupation": None,
        "official_source_url": "https://pmsuryaghar.gov.in",
        "application_url": "https://pmsuryaghar.gov.in/apply",
        "processing_timeline": {
            "expected_days": 15,
            "description": "Technical feasibility approval within 15 working days post DISCOM inspection",
            "is_verified": True
        },
        "required_documents": [
            "Aadhaar Card",
            "Latest Electricity Bill (showing Consumer Number)",
            "Bank Account Passbook or Cancelled Cheque",
            "Proof of House/Roof Ownership"
        ],
        "active": True,
        "rules": [
            {
                "field": "income",
                "operator": "less_than_or_equal",
                "value": "1000000",
                "description": "Applicant must have a suitable roof and active domestic electricity connection."
            }
        ]
    }

    # Temporarily append to seed to verify runtime dynamic discovery
    VERIFIED_SCHEMES_SEED.append(custom_scheme)
    try:
        # Test 1: LanguageService dynamically detects the new scheme
        scheme_id, conf = language_service.detect_scheme_intent("How to apply for PM Surya Ghar solar subsidy?")
        assert scheme_id == "pm-surya-ghar-007"

        # Test in Kannada
        scheme_id_kn, conf_kn = language_service.detect_scheme_intent("ಸೂರ್ಯ ಘರ್ ಯೋಜನೆಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?")
        assert scheme_id_kn == "pm-surya-ghar-007"

        # Test 2: Full conversational turn for the new scheme
        session_id = "surya_ghar_dynamic_sess"
        conversation_service.clear_session(session_id)

        resp = conversation_service.respond(VaniRespondRequest(
            query="Tell me about PM Surya Ghar solar scheme",
            language="en",
            session_id=session_id,
        ))
        assert resp.context_scheme_id == "pm-surya-ghar-007"
        assert "Surya Ghar" in resp.reply_text
        assert "300 units" in resp.reply_text or "Electricity" in resp.reply_text
        assert len(resp.scheme_cards) == 1
        assert resp.scheme_cards[0].scheme_id == "pm-surya-ghar-007"

        # Follow-up on documents
        doc_resp = conversation_service.respond(VaniRespondRequest(
            query="What documents do I need?",
            language="en",
            session_id=session_id,
        ))
        assert doc_resp.context_scheme_id == "pm-surya-ghar-007"
        assert "Electricity Bill" in doc_resp.reply_text

    finally:
        # Clean up appended test scheme
        VERIFIED_SCHEMES_SEED.remove(custom_scheme)


# Test 16: Zero-Hallucination Safe Guard for Unverified / Unknown Schemes
def test_unverified_scheme_non_hallucination():
    session_id = "unverified_scheme_sess"
    conversation_service.clear_session(session_id)

    # Ask about a scheme that does NOT exist in verified GramSetu database
    resp = conversation_service.respond(VaniRespondRequest(
        query="Tell me about Sukanya Samriddhi Yojana",
        language="en",
        session_id=session_id,
    ))

    assert resp.intent == "unverified_scheme_notice"
    # MUST explicitly declare that GramSetu does not have verified info
    assert "does not have verified statutory information" in resp.reply_text
    # MUST NOT hallucinate fake eligibility criteria or claim user is eligible
    assert len(resp.scheme_cards) == 0

    # Kannada unverified query
    resp_kn = conversation_service.respond(VaniRespondRequest(
        query="ಲಾಡ್ಲಿ ಬೆಹನಾ ಯೋಜನೆ ಬಗ್ಗೆ ತಿಳಿಸಿ",
        language="kn",
        session_id="unverified_kn_sess",
    ))
    assert resp_kn.intent == "unverified_scheme_notice"
    assert "ಪರಿಶೀಲಿತ ಶಾಸನಬದ್ಧ ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ" in resp_kn.reply_text


if __name__ == "__main__":
    test_supported_languages_and_normalization()
    test_stt_transcription_validation()
    test_tts_synthesis()
    test_civic_scheme_grounded_response()
    test_multi_turn_context_resolution()
    test_pii_redaction()
    test_unified_conversation_turn()
    test_session_clear()
    test_ration_card_intent_detection()
    test_ration_card_exact_conversation_flow()
    test_ration_card_sub_intent_followups()
    test_ration_card_multilingual_continuity()
    test_unverified_timeline_handling()
    test_multiple_unrelated_schemes_grounded_responses()
    test_dynamic_extensibility_with_new_scheme()
    test_unverified_scheme_non_hallucination()
    print("All Vani-Bot voice engine tests passed successfully!")


