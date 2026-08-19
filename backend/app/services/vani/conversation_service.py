import uuid
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.vani import (
    VaniConverseRequest,
    VaniConverseResponse,
    VaniSchemeCard,
    VaniActionLink,
)
from app.schemas.eligibility import CitizenProfile
from app.data.verified_schemes import VERIFIED_SCHEMES_SEED
from app.services.yojanamatch import yojanamatch_service
from app.services.vani.language_service import language_service
import logging

logger = logging.getLogger(__name__)


class VaniConversationService:
    """
    Grounded Civic Conversation Engine for Vani-Bot.
    Combines verified government scheme catalogs, deterministic YojanaMatch eligibility rules,
    and localized linguistic response synthesis across Kannada, Hindi, and English.
    """

    def __init__(self):
        # In-memory multi-turn session cache
        self._session_history: Dict[str, List[Dict[str, Any]]] = {}
        self._session_scheme_context: Dict[str, str] = {}
        self._session_language_context: Dict[str, str] = {}

    def _get_scheme_by_id(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        for s in VERIFIED_SCHEMES_SEED:
            if s.get("id") == scheme_id:
                return s
        return None

    def _build_scheme_cards(
        self,
        schemes: List[Dict[str, Any]],
        profile: Optional[CitizenProfile] = None,
    ) -> List[VaniSchemeCard]:
        cards: List[VaniSchemeCard] = []
        for s in schemes:
            s_id = str(s.get("id", ""))
            s_name = str(s.get("name", ""))
            benefits = s.get("benefits", [])
            docs = s.get("required_documents", [])
            
            # Evaluate deterministic eligibility if profile provided
            eligible = None
            score = None
            if profile:
                eval_res = yojanamatch_service.evaluate_scheme(s, profile)
                eligible = eval_res.eligible_status
                score = eval_res.match_score

            cards.append(
                VaniSchemeCard(
                    scheme_id=s_id,
                    scheme_name=s_name,
                    category=s.get("category"),
                    state=s.get("state"),
                    short_summary=s.get("short_description", ""),
                    eligible_status=eligible,
                    match_score=score,
                    key_benefits=benefits[:3] if isinstance(benefits, list) else [str(benefits)],
                    required_documents=docs if isinstance(docs, list) else [str(docs)],
                    official_url=s.get("official_source_url", ""),
                    kagazcheck_ready=True,
                )
            )
        return cards

    @classmethod
    def _get_localized_scheme_name(cls, scheme: Dict[str, Any], lang: str) -> str:
        default_name = scheme.get("name", "")
        loc_names = scheme.get("localized_names", {})
        if isinstance(loc_names, dict) and lang in loc_names:
            return loc_names[lang]
        return default_name

    def _format_unverified_scheme_response(self, lang: str) -> str:
        if lang == "kn":
            return (
                "ಗ್ರಾಮಸೇತು ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ಪ್ರಸ್ತುತ ಆ ಯೋಜನೆಗೆ ಸಂಬಂಧಿಸಿದ ಪರಿಶೀಲಿತ ಶಾಸನಬದ್ಧ ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ. "
                "ದಯವಿಟ್ಟು ಅಧಿಕೃತ ಸರಕಾರಿ ಪೋರ್ಟಲ್ ಅಥವಾ ನಿಮ್ಮ ಸ್ಥಳೀಯ ಆಡಳಿತ ಕೇಂದ್ರವನ್ನು (ಗ್ರಾಮ ಪಂಚಾಯತಿ / ಗ್ರಾಮ ಒನ್) ಸಂಪರ್ಕಿಸಿ."
            )
        elif lang == "hi":
            return (
                "ग्रामसेतु डेटाबेस में वर्तमान में उस योजना से संबंधित सत्यापित वैधानिक जानकारी उपलब्ध नहीं है। "
                "कृपया आधिकारिक सरकारी पोर्टल अथवा अपने स्थानीय प्रशासनिक केंद्र (ग्राम पंचायत / जन सेवा केंद्र) से संपर्क करें।"
            )
        else:
            return (
                "GramSetu currently does not have verified statutory information for that scheme in its database. "
                "Please consult official government portals or your local administrative centre (Gram Panchayat / CSC Kendra) for verified details."
            )

    def _format_scheme_overview(self, scheme: Dict[str, Any], lang: str) -> str:
        s_name = self._get_localized_scheme_name(scheme, lang)
        docs = scheme.get("required_documents", [])
        rules = scheme.get("rules", [])
        app_url = scheme.get("application_url") or scheme.get("official_source_url", "")

        elig_lines = [r.get("description", "") for r in rules if r.get("description")]
        if not elig_lines:
            elig_lines = [scheme.get("short_description", "")]

        if lang == "kn":
            elig_txt = "\n".join([f"• {e}" for e in elig_lines])
            docs_txt = "\n".join([f"• {d}" for d in docs])
            return (
                f"ಖಂಡಿತ, **{s_name}** ಕುರಿತ ಪರಿಶೀಲಿತ ಮಾಹಿತಿ ಇಲ್ಲಿದೆ:\n\n"
                f"**ಅರ್ಹತಾ ಮಾನದಂಡಗಳು:**\n{elig_txt}\n\n"
                f"**ಅಗತ್ಯವಿರುವ ಮುಖ್ಯ ದಾಖಲೆಗಳು:**\n{docs_txt}\n\n"
                f"**ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ವಿಧಾನ:**\n"
                f"• ಆನ್‌ಲೈನ್ ಪೋರ್ಟಲ್: {app_url}\n"
                f"• ಹತ್ತಿರದ ಗ್ರಾಮ ಒನ್ (Gram One) / ಸಿಎಸ್‌ಸಿ ಕೇಂದ್ರ ಅಥವಾ ಸಂಬಂಧಪಟ್ಟ ಸರಕಾರಿ ಕಚೇರಿಯಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು.\n\n"
                f"ನಿಮ್ಮ ದಾಖಲೆಗಳನ್ನು ಕಾಗಜ್‌ಚೆಕ್ (KagazCheck) ಮೂಲಕ ಪರಿಶೀಲಿಸಲು ಕೆಳಗಿನ ಬಟನ್ ಬಳಸಿ."
            )
        elif lang == "hi":
            elig_txt = "\n".join([f"• {e}" for e in elig_lines])
            docs_txt = "\n".join([f"• {d}" for d in docs])
            return (
                f"अवश्य, **{s_name}** के लिए उपलब्ध सत्यापित विवरण निम्नलिखित हैं:\n\n"
                f"**पात्रता मानदंड:**\n{elig_txt}\n\n"
                f"**आवश्यक प्रमुख दस्तावेज:**\n{docs_txt}\n\n"
                f"**आवेदन प्रक्रिया:**\n"
                f"• आधिकारिक पोर्टल: {app_url}\n"
                f"• नजदीकी जन सेवा केंद्र (CSC Kendra), ग्राम वन, या संबंधित सरकारी कार्यालय में आवेदन करें।\n\n"
                f"आप अपने दस्तावेजों की शुद्धता कागज़चेक (KagazCheck) द्वारा सत्यापित कर सकते हैं।"
            )
        else:
            elig_txt = "\n".join([f"• {e}" for e in elig_lines])
            docs_txt = "\n".join([f"• {d}" for d in docs])
            return (
                f"Sure. I can help you with **{s_name}**.\n\n"
                f"Here are the verified details currently available:\n\n"
                f"**Eligibility:**\n{elig_txt}\n\n"
                f"**Required Documents:**\n{docs_txt}\n\n"
                f"**Application Process:**\n"
                f"• Online Portal: {app_url}\n"
                f"• Offline: Visit your nearest Gram One centre, Common Service Centre (CSC), or designated government office.\n\n"
                f"You can verify your statutory documents using KagazCheck before applying."
            )

    def converse(self, req: VaniConverseRequest) -> VaniConverseResponse:
        """
        Processes a voice/text turn, performs grounded scheme reasoning, and returns response in requested language.
        """
        session_id = req.session_id or f"vani_sess_{uuid.uuid4().hex[:10]}"
        query = req.user_query.strip() if req.user_query else ""
        
        detected_script_lang = language_service.detect_language_from_text(query, default_lang=req.language or "en")
        if session_id in self._session_language_context and detected_script_lang == "en" and req.language == "kn":
            lang = self._session_language_context[session_id]
        else:
            lang = detected_script_lang
        self._session_language_context[session_id] = lang

        # Build CitizenProfile object if profile dict passed
        profile_obj: Optional[CitizenProfile] = None
        if req.citizen_profile:
            try:
                profile_obj = CitizenProfile(**req.citizen_profile)
            except Exception as e:
                logger.warning(f"Could not parse citizen profile in Vani-Bot: {e}")

        valid_scheme_ids = [s["id"] for s in VERIFIED_SCHEMES_SEED]

        # Detect intent and scheme association
        matched_scheme_id, confidence = language_service.detect_scheme_intent(query)
        if not matched_scheme_id:
            if req.context_scheme_id and req.context_scheme_id in valid_scheme_ids:
                matched_scheme_id = req.context_scheme_id
            elif session_id in self._session_scheme_context:
                matched_scheme_id = self._session_scheme_context[session_id]

        sub_intent = language_service.classify_sub_intent(query)

        if matched_scheme_id and matched_scheme_id in valid_scheme_ids:
            self._session_scheme_context[session_id] = matched_scheme_id

        # Response construction components
        reply_text = ""
        scheme_cards: List[VaniSchemeCard] = []
        action_links: List[VaniActionLink] = []
        sources: List[str] = []
        suggested_followups: List[str] = []

        # -------------------------------------------------------------
        # SCENARIO 0: Unverified Scheme Query
        # -------------------------------------------------------------
        if matched_scheme_id == "unverified_scheme":
            reply_text = self._format_unverified_scheme_response(lang)
            sources = ["GramSetu Verification Engine"]
            suggested_followups = [
                "Which schemes am I eligible for?",
                "What documents do I need for PM-KISAN?",
                "How to apply for Ration Card?",
            ]

        # -------------------------------------------------------------
        # SCENARIO 1: Specific Scheme Query
        # -------------------------------------------------------------
        elif matched_scheme_id and matched_scheme_id in valid_scheme_ids:
            target_scheme = self._get_scheme_by_id(matched_scheme_id)
            if target_scheme:
                scheme_cards = self._build_scheme_cards([target_scheme], profile_obj)
                sources = [target_scheme.get("official_source_url", "Official Gazette")]
                s_name = self._get_localized_scheme_name(target_scheme, lang)

                if sub_intent == "documents":
                    docs = target_scheme.get("required_documents", [])
                    docs_txt = "\n".join([f"• {d}" for d in docs])
                    if lang == "kn":
                        reply_text = f"**{s_name}** ಗೆ ಅಗತ್ಯವಿರುವ ದಾಖಲೆಗಳು:\n\n{docs_txt}"
                    elif lang == "hi":
                        reply_text = f"**{s_name}** के आवश्यक दस्तावेज:\n\n{docs_txt}"
                    else:
                        reply_text = f"Required documents for **{s_name}**:\n\n{docs_txt}"
                elif sub_intent == "application":
                    app_url = target_scheme.get("application_url") or target_scheme.get("official_source_url", "")
                    if lang == "kn":
                        reply_text = f"**{s_name}** ಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ಅಧಿಕೃತ ಪೋರ್ಟಲ್: {app_url} ಅಥವಾ ಹತ್ತಿರದ ಗ್ರಾಮ ಒನ್ / ಸಿಎಸ್‌ಸಿ ಕೇಂದ್ರ."
                    elif lang == "hi":
                        reply_text = f"**{s_name}** के लिए आधिकारिक पोर्टल: {app_url} या नजदीकी जन सेवा केंद्र पर आवेदन करें।"
                    else:
                        reply_text = f"Apply for **{s_name}** online at {app_url} or offline at your nearest CSC / Gram One centre."
                else:
                    reply_text = self._format_scheme_overview(target_scheme, lang)

                suggested_followups = [
                    f"What documents do I need for {s_name.split('(')[0].strip()}?",
                    f"Where do I apply?",
                    f"Am I eligible for {s_name.split('(')[0].strip()}?",
                ]
                action_links.append(
                    VaniActionLink(
                        label="Audit Documents on KagazCheck" if lang == "en" else ("ಕಾಗಜ್‌ಚೆಕ್‌ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ" if lang == "kn" else "कागज़चेक में जांचें"),
                        action_type="open_kagazcheck",
                        payload={"scheme_id": matched_scheme_id},
                    )
                )


        # -------------------------------------------------------------
        # SCENARIO 2: General Eligibility Query
        # -------------------------------------------------------------
        elif sub_intent == "eligibility" or any(w in query.lower() for w in ["which", "eligible", "qualify", "ಯಾವ", "ಸಿಗುತ್ತದೆ", "पात्र"]):
            if profile_obj:
                match_resp = yojanamatch_service.match_citizen(profile_obj)
                eligible_schemes = [self._get_scheme_by_id(r.scheme_id) for r in match_resp.results if r.eligible_status and self._get_scheme_by_id(r.scheme_id)]
                if not eligible_schemes:
                    eligible_schemes = VERIFIED_SCHEMES_SEED[:2]
                scheme_cards = self._build_scheme_cards(eligible_schemes[:3], profile_obj)
                sources = ["GramSetu YojanaMatch Deterministic Engine"]

                s_names_kn = ", ".join([s["name"].split("(")[0].strip() for s in eligible_schemes[:3]])
                s_names_hi = ", ".join([s["name"].split("(")[0].strip() for s in eligible_schemes[:3]])
                s_names_en = ", ".join([s["name"].split("(")[0].strip() for s in eligible_schemes[:3]])

                if lang == "kn":
                    reply_text = (
                        f"ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಪರಿಶೀಲಿಸಲಾಗಿದ್ದು, ನೀವು **{len(eligible_schemes)} ಪರಿಶೀಲಿತ ಯೋಜನೆಗಳಿಗೆ** ಅರ್ಹರಾಗಿದ್ದೀರಿ:\n\n"
                        f"• {s_names_kn}.\n\n"
                        f"ಯೋಜನೆಯ ವಿವರ ಹಾಗೂ ಕಾಗಜ್‌ಚೆಕ್ ಮೂಲಕ ದಾಖಲೆ ಪರಿಶೀಲನೆ ಮಾಡಲು ಕೆಳಗಿನ ಕಾರ್ಡ್‌ಗಳನ್ನು ನೋಡಿ."
                    )
                    suggested_followups = ["ರೇಷನ್ ಕಾರ್ಡ್ ಮಾಹಿತಿ", "ಪಿಎಂ ಕಿಸಾನ್ ಬಗ್ಗೆ ತಿಳಿಸಿ", "ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ"]
                elif lang == "hi":
                    reply_text = (
                        f"आपकी प्रोफाइल के आधार पर आप **{len(eligible_schemes)} सत्यापित योजनाओं** के लिए पात्र हैं:\n\n"
                        f"• {s_names_hi}।\n\n"
                        f"विस्तृत जानकारी और कागज़ात जांच के लिए नीचे दिए गए कार्ड्स देखें।"
                    )
                    suggested_followups = ["राशन कार्ड की जानकारी", "पीएम किसान की जानकारी", "कागजात की जांच करें"]
                else:
                    reply_text = (
                        f"Based on your profile, you qualify for **{len(eligible_schemes)} verified schemes**:\n\n"
                        f"• {s_names_en}.\n\n"
                        f"Check the cards below for benefits, eligibility rules, and document verification."
                    )
                    suggested_followups = ["Explain Ration Card rules", "Explain PM-KISAN rules", "Audit my documents"]
            else:
                top_schemes = VERIFIED_SCHEMES_SEED[:3]
                scheme_cards = self._build_scheme_cards(top_schemes)
                sources = ["GramSetu Schemes Repository"]

                if lang == "kn":
                    reply_text = (
                        "ಗ್ರಾಮಸೇತು ಎಐ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಪ್ರಮುಖವಾಗಿ ರೇಷನ್ ಕಾರ್ಡ್, ಪಿಎಂ ಕಿಸಾನ್, ಪಿಎಂ ಆವಾಸ್ ಗ್ರಾಮೀಣ, ಮತ್ತು ಆಯುಷ್ಮಾನ್ ಭಾರತ್ ಯೋಜನೆಗಳು ಲಭ್ಯವಿವೆ."
                    )
                elif lang == "hi":
                    reply_text = (
                        "ग्रामसेतु एआई पर प्रमुख योजनाएं जैसे राशन कार्ड, पीएम किसान, पीएम आवास ग्रामीण और आयुष्मान भारत उपलब्ध हैं।"
                    )
                else:
                    reply_text = (
                        "GramSetu AI features verified statutory welfare schemes including Ration Card, PM-KISAN, PMAY-G, and PM-JAY."
                    )

            action_links.append(
                VaniActionLink(
                    label="Find All Eligible Schemes" if lang == "en" else ("ಅರ್ಹ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ" if lang == "kn" else "पात्र योजनाएं खोजें"),
                    action_type="check_eligibility",
                    payload={},
                )
            )

        # -------------------------------------------------------------
        # SCENARIO 3: Document Inquiry
        # -------------------------------------------------------------
        elif sub_intent == "documents":
            all_docs_schemes = VERIFIED_SCHEMES_SEED[:2]
            scheme_cards = self._build_scheme_cards(all_docs_schemes, profile_obj)
            sources = ["KagazCheck Statutory Document Standards"]

            if lang == "kn":
                reply_text = (
                    "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳಿಗೆ ಮುಖ್ಯವಾಗಿ ಆಧಾರ್ ಕಾರ್ಡ್, ರೇಷನ್ ಕಾರ್ಡ್, ಜಮೀನಿನ ಪಹಣಿ (ROR), ಮತ್ತು ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್ ಅಗತ್ಯವಿರುತ್ತದೆ."
                )
            elif lang == "hi":
                reply_text = (
                    "सरकारी योजनाओं के आवेदन के लिए मुख्य रूप से आधार कार्ड, राशन कार्ड, जमीन का खसरा/खतौनी, और बैंक पासबुक आवश्यक हैं।"
                )
            else:
                reply_text = (
                    "Standard government welfare schemes require Aadhaar Card, Ration/BPL Card, Land RoR, and Bank Passbook."
                )

            action_links.append(
                VaniActionLink(
                    label="Open KagazCheck Auditor" if lang == "en" else ("ಕಾಗಜ್‌ಚೆಕ್ ಕ್ಯಾಮೆರಾ ತೆರೆಯಿರಿ" if lang == "kn" else "कागज़चेक कैमरा खोलें"),
                    action_type="open_kagazcheck",
                    payload={},
                )
            )

        # -------------------------------------------------------------
        # SCENARIO 4: General Civic Inquiries / Polite Help
        # -------------------------------------------------------------
        else:
            top_schemes = VERIFIED_SCHEMES_SEED[:2]
            scheme_cards = self._build_scheme_cards(top_schemes, profile_obj)
            sources = ["GramSetu AI Grounded Intelligence"]

            if lang == "kn":
                reply_text = (
                    "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಗ್ರಾಮಸೇತು ಧ್ವನಿ ಸಹಾಯಕ (Vani-Bot). "
                    "ನೀವು ರೇಷನ್ ಕಾರ್ಡ್, ಕಿಸಾನ್ ಯೋಜನೆ, ಆವಾಸ್ ಯೋಜನೆ ಕುರಿತು ಧ್ವನಿಯಲ್ಲೇ ಕೇಳಬಹುದು."
                )
                suggested_followups = ["ರೇಷನ್ ಕಾರ್ಡ್ ಅರ್ಜಿ ಹೇಗೆ?", "ಪಿಎಂ ಕಿಸಾನ್ ದಾಖಲೆಗಳು ಯಾವುವು?"]
            elif lang == "hi":
                reply_text = (
                    "नमस्ते! मैं आपका ग्रामसेतु वाणी सहायक (Vani-Bot) हूँ। "
                    "आप राशन कार्ड, किसान योजना, या आवास योजना के बारे में सीधे पूछ सकते हैं।"
                )
                suggested_followups = ["राशन कार्ड कैसे बनवाएं?", "पीएम किसान के दस्तावेज"]
            else:
                reply_text = (
                    "Namaste! I am your GramSetu Vani Voice Assistant. "
                    "You can ask about Ration Card, PM-KISAN, PMAY-G Housing, or PM-JAY Health."
                )
                suggested_followups = ["I want to apply for ration card", "What documents are needed for PM-KISAN?"]

        # Record in session history
        turn_data = {
            "query": query,
            "reply": reply_text,
            "language": lang,
        }
        if session_id not in self._session_history:
            self._session_history[session_id] = []
        self._session_history[session_id].append(turn_data)
        if len(self._session_history[session_id]) > 10:
            self._session_history[session_id].pop(0)

        return VaniConverseResponse(
            session_id=session_id,
            user_query=query,
            language=lang,
            detected_intent=matched_scheme_id or "general_inquiry",
            reply_text=reply_text,
            scheme_cards=scheme_cards,
            action_links=action_links,
            sources=sources,
            suggested_followups=suggested_followups,
        )

    def clear_session(self, session_id: str):
        if session_id in self._session_history:
            del self._session_history[session_id]
        if session_id in self._session_scheme_context:
            del self._session_scheme_context[session_id]
        if session_id in self._session_language_context:
            del self._session_language_context[session_id]


conversation_service = VaniConversationService()

