import uuid
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

from app.schemas.vanibot import (
    VaniRespondRequest,
    VaniRespondResponse,
    VaniSchemeCard,
    VaniActionLink,
)
from app.schemas.eligibility import CitizenProfile
from app.data.verified_schemes import VERIFIED_SCHEMES_SEED
from app.services.yojanamatch import yojanamatch_service
from app.services.vanibot.language_service import language_service

logger = logging.getLogger(__name__)


class VaniConversationService:
    """
    Grounded Civic Conversation Engine for Vani-Bot.
    Combines verified government scheme data, deterministic YojanaMatch eligibility rules,
    multi-turn context resolution, and localized linguistic response synthesis across Kannada, Hindi, and English.
    """

    def __init__(self):
        # Bounded in-memory multi-turn session cache
        self._session_history: Dict[str, List[Dict[str, Any]]] = {}
        self._session_scheme_context: Dict[str, str] = {}
        self._session_language_context: Dict[str, str] = {}
        self._session_intent_context: Dict[str, str] = {}

    def _redact_pii(self, text: str) -> str:
        """
        Privacy filter: Masks sensitive 12-digit Aadhaar numbers and bank account numbers.
        """
        if not text:
            return ""
        # Redact 12-digit Aadhaar patterns (e.g. 9999 4105 7058 or 999941057058)
        text = re.sub(r"\b(\d{4})[\s-]?(\d{4})[\s-](\d{4})\b", r"XXXX-XXXX-\3", text)
        # Redact lone 12-digit numbers
        text = re.sub(r"\b\d{8}(\d{4})\b", r"XXXX-XXXX-\1", text)
        return text

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
        """
        Builds a structured, grounded overview of a specific verified scheme covering
        Eligibility, Required Documents, and Application channels.
        """
        s_name = self._get_localized_scheme_name(scheme, lang)
        benefits = scheme.get("benefits", [])
        docs = scheme.get("required_documents", [])
        rules = scheme.get("rules", [])
        app_url = scheme.get("application_url") or scheme.get("official_source_url", "")

        # Format rules/eligibility lines
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

    def _format_document_response(self, scheme: Dict[str, Any], lang: str) -> str:
        s_name = self._get_localized_scheme_name(scheme, lang)
        docs = scheme.get("required_documents", [])
        docs_txt = "\n".join([f"• {d}" for d in docs])

        if lang == "kn":
            return (
                f"**{s_name}** ಗೆ ಅಗತ್ಯವಿರುವ ಪರಿಶೀಲಿತ ಶಾಸನಬದ್ಧ ದಾಖಲೆಗಳು:\n\n"
                f"{docs_txt}\n\n"
                f"ಈ ದಾಖಲೆಗಳನ್ನು ನೀವು ಕಾಗಜ್‌ಚೆಕ್ (KagazCheck) ನಲ್ಲಿ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ತಕ್ಷಣ ಪರಿಶೀಲಿಸಬಹುದು."
            )
        elif lang == "hi":
            return (
                f"**{s_name}** के लिए आवश्यक सत्यापित वैधानिक दस्तावेज निम्नलिखित हैं:\n\n"
                f"{docs_txt}\n\n"
                f"आप इन दस्तावेजों की वैधता कागज़चेक (KagazCheck) से जांच सकते हैं।"
            )
        else:
            return (
                f"For **{s_name}**, the required statutory documents are:\n\n"
                f"{docs_txt}\n\n"
                f"You can audit your certificates with KagazCheck before applying."
            )

    def _format_application_response(self, scheme: Dict[str, Any], lang: str) -> str:
        s_name = self._get_localized_scheme_name(scheme, lang)
        app_url = scheme.get("application_url") or scheme.get("official_source_url", "")
        docs_str = ", ".join(scheme.get("required_documents", [])[:3])

        if lang == "kn":
            return (
                f"**{s_name}** ಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ಅಧಿಕೃತ ವಿಧಾನ:\n\n"
                f"1. ಅಗತ್ಯ ದಾಖಲೆಗಳನ್ನು ಸಿದ್ಧಪಡಿಸಿಕೊಳ್ಳಿ ({docs_str}).\n"
                f"2. ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಅಧಿಕೃತ ಪೋರ್ಟಲ್: {app_url}\n"
                f"3. ಹತ್ತಿರದ ಗ್ರಾಮ ಒನ್ (Gram One) ಅಥವಾ ಸಿಎಸ್‌ಸಿ (CSC) ಕೇಂದ್ರದಲ್ಲಿ ಬಯೋಮೆಟ್ರಿಕ್ / ಒಟಿಪಿ ದೃಢೀಕರಣದೊಂದಿಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.\n"
                f"4. ಅರ್ಜಿ ಸಲ್ಲಿಸಿದ ನಂತರ ಸ್ವೀಕೃತಿ ರಶೀದಿಯನ್ನು ಪಡೆದು ಸ್ಥಿತಿಯನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ."
            )
        elif lang == "hi":
            return (
                f"**{s_name}** के लिए आवेदन करने की आधिकारिक प्रक्रिया:\n\n"
                f"1. आवश्यक दस्तावेज तैयार करें ({docs_str})।\n"
                f"2. ऑनलाइन आवेदन के लिए आधिकारिक पोर्टल: {app_url}\n"
                f"3. नजदीकी जन सेवा केंद्र (CSC Kendra) या ग्राम वन में बायोमेट्रिक/ओटीपी सत्यापन के साथ आवेदन करें।\n"
                f"4. आवेदन जमा करने के बाद रसीद प्राप्त करें और स्थिति ट्रैक करें।"
            )
        else:
            return (
                f"How and where to apply for **{s_name}**:\n\n"
                f"1. Prepare your statutory documents ({docs_str}).\n"
                f"2. Online Application: Apply via the official portal at {app_url}\n"
                f"3. Offline / Citizen Centre: Visit your nearest Gram One centre, Common Service Centre (CSC), or administrative office.\n"
                f"4. Complete biometric / OTP authentication upon submission and retain the acknowledgment receipt."
            )

    def _format_timeline_response(self, scheme: Dict[str, Any], lang: str) -> str:
        s_name = self._get_localized_scheme_name(scheme, lang)

        timeline_data = scheme.get("processing_timeline")
        if not timeline_data:
            from app.services.parchaa.data_service import VERIFIED_SCHEME_METADATA
            meta = VERIFIED_SCHEME_METADATA.get(scheme.get("id", ""), {})
            timeline_data = meta.get("processing_timeline")

        if isinstance(timeline_data, dict) and timeline_data.get("is_verified", False):
            desc = timeline_data.get("timeline_description") or timeline_data.get("description", "")
            days = timeline_data.get("expected_days")
            if days and desc:
                if lang == "kn":
                    return f"**{s_name}** ಯೋಜನೆಯ ಪರಿಶೀಲಿತ ವಿಲೇವಾರಿ ಕಾಲಾವಕಾಶ: ಸುಮಾರು {days} ದಿನಗಳು ({desc})."
                elif lang == "hi":
                    return f"**{s_name}** के लिए सत्यापित प्रसंस्करण समय-सीमा: लगभग {days} दिन ({desc})।"
                else:
                    return f"For **{s_name}**, the verified statutory processing timeline is approximately {days} days ({desc})."
            elif days:
                if lang == "kn":
                    return f"**{s_name}** ಯೋಜನೆಯ ಪರಿಶೀಲಿತ ವಿಲೇವಾರಿ ಕಾಲಾವಕಾಶ: ಸುಮಾರು {days} ದಿನಗಳು."
                elif lang == "hi":
                    return f"**{s_name}** के लिए सत्यापित प्रसंस्करण समय-सीमा: लगभग {days} दिन।"
                else:
                    return f"For **{s_name}**, the verified statutory processing timeline is approximately {days} days."
            elif desc:
                if lang == "kn":
                    return f"**{s_name}** ಯೋಜನೆಯ ಪರಿಶೀಲಿತ ವಿಲೇವಾರಿ ಮಾಹಿತಿ: {desc}"
                elif lang == "hi":
                    return f"**{s_name}** के लिए सत्यापित प्रसंस्करण विवरण: {desc}"
                else:
                    return f"For **{s_name}**, the verified processing timeline is: {desc}"
            else:
                if lang == "kn":
                    return f"**{s_name}** ಯೋಜನೆಯ ನಿಖರವಾದ ಶಾಸನಬದ್ಧ ವಿಲೇವಾರಿ ಕಾಲಾವಧಿಯು ಪ್ರಸ್ತುತ ಪರಿಶೀಲಿತ ಗ್ರಾಮಸೇತು ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ಲಭ್ಯವಿಲ್ಲ. ಸಂಬಂಧಪಟ್ಟ ಇಲಾಖೆಯ ನಿಯಮಾವಳಿಗಳನ್ನು ಪರಿಶೀಲಿಸಿ."
                elif lang == "hi":
                    return f"**{s_name}** के लिए विशिष्ट वैधानिक प्रसंस्करण समय-सीमा वर्तमान सत्यापित ग्रामसेतु डेटाबेस में उपलब्ध नहीं है। कृपया विभागीय दिशा-निर्देश देखें।"
                else:
                    return f"The specific statutory processing timeline for **{s_name}** is not available in the current verified GramSetu database."

        elif isinstance(timeline_data, str) and timeline_data.strip():
            if lang == "kn":
                return f"**{s_name}** ಯೋಜನೆಯ ಪರಿಶೀಲಿತ ವಿಲೇವಾರಿ ಕಾಲಾವಕಾಶ: {timeline_data}"
            elif lang == "hi":
                return f"**{s_name}** के लिए सत्यापित प्रसंस्करण विवरण: {timeline_data}"
            else:
                return f"For **{s_name}**, the verified statutory processing timeline is: {timeline_data}"
        else:
            if lang == "kn":
                return f"**{s_name}** ಯೋಜನೆಯ ನಿಖರವಾದ ಶಾಸನಬದ್ಧ ವಿಲೇವಾರಿ ಕಾಲಾವಧಿಯು ಪ್ರಸ್ತುತ ಪರಿಶೀಲಿತ ಗ್ರಾಮಸೇತು ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ಲಭ್ಯವಿಲ್ಲ. ಸಂಬಂಧಪಟ್ಟ ಇಲಾಖೆಯ ನಿಯಮಾವಳಿಗಳನ್ನು ಪರಿಶೀಲಿಸಿ."
            elif lang == "hi":
                return f"**{s_name}** के लिए विशिष्ट वैधानिक प्रसंस्करण समय-सीमा वर्तमान सत्यापित ग्रामसेतु डेटाबेस में उपलब्ध नहीं है। कृपया विभागीय दिशा-निर्देश देखें।"
            else:
                return f"The specific statutory processing timeline for **{s_name}** is not available in the current verified GramSetu database."


    def _format_eligibility_response(
        self,
        scheme: Dict[str, Any],
        profile_obj: Optional[CitizenProfile],
        lang: str,
    ) -> str:
        s_name = self._get_localized_scheme_name(scheme, lang)
        rules = scheme.get("rules", [])

        
        # If profile available, run deterministic evaluation
        if profile_obj:
            eval_res = yojanamatch_service.evaluate_scheme(scheme, profile_obj)
            if eval_res.eligible_status:
                if lang == "kn":
                    return f"ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಅನ್ನು ಪರಿಶೀಲಿಸಲಾಗಿದ್ದು, ನೀವು **{s_name}** ಯೋಜನೆಗೆ ಸಂಪೂರ್ಣವಾಗಿ ಅರ್ಹರಾಗಿದ್ದೀರಿ."
                elif lang == "hi":
                    return f"आपकी प्रोफाइल के आधार पर आप **{s_name}** के लिए पूर्णतः पात्र हैं।"
                else:
                    return f"Based on your profile, you meet all deterministic criteria and are eligible for **{s_name}**."
            else:
                failed = [r.description for r in eval_res.failed_rules if r.description]
                fail_str = failed[0] if failed else "ಮಾನದಂಡಗಳು ಹೊಂದಿಲ್ಲ"
                if lang == "kn":
                    return f"ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಪ್ರಕಾರ: {fail_str}. ಈ ಯೋಜನೆಯ ಮಾನದಂಡಗಳನ್ನು ಪರಿಶೀಲಿಸಿ."
                elif lang == "hi":
                    return f"आपकी प्रोफाइल के अनुसार: {fail_str}। कृपया योजना की शर्तें जांचें।"
                else:
                    return f"Based on your profile: {fail_str}. Please review the scheme eligibility criteria."
        else:
            # Explain rules clearly without assuming profile values
            rule_descs = [r.get("description", "") for r in rules if r.get("description")]
            rules_txt = "\n".join([f"• {d}" for d in rule_descs])
            if lang == "kn":
                return f"**{s_name}** ನ ಅರ್ಹತಾ ಮಾನದಂಡಗಳು:\n\n{rules_txt}"
            elif lang == "hi":
                return f"**{s_name}** के पात्रता नियम:\n\n{rules_txt}"
            else:
                return f"Eligibility criteria for **{s_name}**:\n\n{rules_txt}"

    def respond(self, req: VaniRespondRequest) -> VaniRespondResponse:
        """
        Processes a conversational civic query turn, performs grounded reasoning, and returns response.
        """
        session_id = req.session_id or f"vani_sess_{uuid.uuid4().hex[:10]}"
        query_raw = req.query.strip() if req.query else ""
        query = self._redact_pii(query_raw)

        # Detect language from input text or fallback to request language / session language
        detected_script_lang = language_service.detect_language_from_text(query, default_lang=req.language or "en")
        
        # If user explicitly specified language or previously had language in session
        if session_id in self._session_language_context and detected_script_lang == "en" and req.language == "kn":
            lang = self._session_language_context[session_id]
        else:
            lang = detected_script_lang

        # Save active language in session
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
        
        # Context resolution: only if query did not identify a scheme or explicit unverified inquiry
        if not matched_scheme_id:
            if req.context_scheme_id and req.context_scheme_id in valid_scheme_ids:
                matched_scheme_id = req.context_scheme_id
            elif session_id in self._session_scheme_context:
                matched_scheme_id = self._session_scheme_context[session_id]

        # Classify sub-intent (details, documents, application, eligibility, timeline, benefits, general)
        sub_intent = language_service.classify_sub_intent(query)

        # Update session scheme context if matched with a valid scheme
        if matched_scheme_id and matched_scheme_id in valid_scheme_ids:
            self._session_scheme_context[session_id] = matched_scheme_id

        # Response construction components
        reply_text = ""
        scheme_cards: List[VaniSchemeCard] = []
        action_links: List[VaniActionLink] = []
        sources: List[str] = []
        suggested_followups: List[str] = []
        intent = "scheme_query" if matched_scheme_id else "civic_assistance"

        # -------------------------------------------------------------
        # SCENARIO 0: Unverified Scheme Inquired (Zero-Hallucination Safe Guard)
        # -------------------------------------------------------------
        if matched_scheme_id == "unverified_scheme":
            intent = "unverified_scheme_notice"
            reply_text = self._format_unverified_scheme_response(lang)
            sources = ["GramSetu Verification Engine"]
            suggested_followups = [
                "Which schemes am I eligible for?",
                "What documents do I need for PM-KISAN?",
                "How to apply for Ration Card?",
            ] if lang == "en" else (
                [
                    "ನನಗೆ ಯಾವ ಯೋಜನೆಗಳು ಸಿಗುತ್ತವೆ?",
                    "ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
                    "ರೇಷನ್ ಕಾರ್ಡ್ಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?",
                ] if lang == "kn" else [
                    "मैं किन योजनाओं के लिए पात्र हूँ?",
                    "पीएम किसान के लिए दस्तावेज क्या हैं?",
                    "राशन कार्ड कैसे बनवाएं?",
                ]
            )

        # -------------------------------------------------------------
        # SCENARIO 1: Specific Scheme Query (in focus or follow-up)
        # -------------------------------------------------------------
        elif matched_scheme_id and matched_scheme_id in valid_scheme_ids:
            target_scheme = self._get_scheme_by_id(matched_scheme_id)
            if target_scheme:
                scheme_cards = self._build_scheme_cards([target_scheme], profile_obj)
                sources = [target_scheme.get("official_source_url", "Official Gazette")]
                s_name = target_scheme.get("name", "")


                if sub_intent == "documents":
                    intent = "document_inquiry"
                    reply_text = self._format_document_response(target_scheme, lang)
                    if lang == "kn":
                        suggested_followups = [
                            f"ನನಗೆ {s_name.split('(')[0].strip()} ಸಿಗುತ್ತದೆಯೇ?",
                            "ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಎಲ್ಲಿಗೆ ಹೋಗಬೇಕು?",
                            "ಯೋಜನೆಯ ಪ್ರಯೋಜನವೇನು?",
                        ]
                    elif lang == "hi":
                        suggested_followups = [
                            f"क्या मैं {s_name.split('(')[0].strip()} के लिए पात्र हूँ?",
                            "आवेदन कहाँ और कैसे करें?",
                            "इस योजना के लाभ क्या हैं?",
                        ]
                    else:
                        suggested_followups = [
                            f"Am I eligible for {s_name.split('(')[0].strip()}?",
                            "Where do I apply?",
                            "How long does it take?",
                        ]

                elif sub_intent == "application":
                    intent = "application_guidance"
                    reply_text = self._format_application_response(target_scheme, lang)
                    if lang == "kn":
                        suggested_followups = [
                            f"{s_name.split('(')[0].strip()} ಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
                            "ಕಾಗಜ್‌ಚೆಕ್‌ನಲ್ಲಿ ದಾಖಲೆ ಪರಿಶೀಲಿಸಿ",
                            "ಅರ್ಹತಾ ನಿಯಮಗಳನ್ನು ತಿಳಿಸಿ",
                        ]
                    elif lang == "hi":
                        suggested_followups = [
                            f"{s_name.split('(')[0].strip()} के लिए दस्तावेज क्या हैं?",
                            "दस्तावेज ऑडिट करें (KagazCheck)",
                            "पात्रता की शर्तें क्या हैं?",
                        ]
                    else:
                        suggested_followups = [
                            f"What documents do I need for {s_name.split('(')[0].strip()}?",
                            "Audit documents with KagazCheck",
                            "Am I eligible?",
                        ]

                elif sub_intent == "timeline":
                    intent = "timeline_inquiry"
                    reply_text = self._format_timeline_response(target_scheme, lang)
                    if lang == "kn":
                        suggested_followups = [
                            "ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?",
                            "ದಾಖಲೆಗಳು ಯಾವುವು?",
                        ]
                    elif lang == "hi":
                        suggested_followups = [
                            "आवेदन कैसे करें?",
                            "दस्तावेज क्या हैं?",
                        ]
                    else:
                        suggested_followups = [
                            "How do I apply?",
                            "What documents do I need?",
                        ]

                elif sub_intent == "eligibility":
                    intent = "eligibility_inquiry"
                    reply_text = self._format_eligibility_response(target_scheme, profile_obj, lang)
                    if lang == "kn":
                        suggested_followups = [
                            "ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
                            "ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?",
                        ]
                    elif lang == "hi":
                        suggested_followups = [
                            "आवश्यक दस्तावेज क्या हैं?",
                            "आवेदन कहाँ करें?",
                        ]
                    else:
                        suggested_followups = [
                            "What documents do I need?",
                            "Where do I apply?",
                        ]

                elif sub_intent == "benefits":
                    intent = "benefit_inquiry"
                    b_list = target_scheme.get("benefits", [])
                    b_txt = "\n".join([f"• {b}" for b in b_list])
                    if lang == "kn":
                        reply_text = f"**{s_name}** ಯೋಜನೆಯ ಮುಖ್ಯ ಪ್ರಯೋಜನಗಳು:\n\n{b_txt}"
                        suggested_followups = [f"{s_name.split('(')[0].strip()} ಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?", "ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?"]
                    elif lang == "hi":
                        reply_text = f"**{s_name}** के तहत मिलने वाले मुख्य लाभ:\n\n{b_txt}"
                        suggested_followups = [f"{s_name.split('(')[0].strip()} के लिए दस्तावेज क्या हैं?", "आवेदन कैसे करें?"]
                    else:
                        reply_text = f"Key statutory benefits under **{s_name}**:\n\n{b_txt}"
                        suggested_followups = [f"What documents are required for {s_name.split('(')[0].strip()}?", "How do I apply?"]

                else:
                    # Comprehensive overview / details / initial request
                    intent = "scheme_summary"
                    reply_text = self._format_scheme_overview(target_scheme, lang)
                    if lang == "kn":
                        suggested_followups = [
                            f"{s_name.split('(')[0].strip()} ಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
                            "ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?",
                            "ಕಾಗಜ್‌ಚೆಕ್‌ನಲ್ಲಿ ದಾಖಲೆ ಪರಿಶೀಲಿಸಿ",
                        ]
                    elif lang == "hi":
                        suggested_followups = [
                            f"{s_name.split('(')[0].strip()} के लिए दस्तावेज क्या हैं?",
                            "आवेदन कहाँ और कैसे करें?",
                            "दस्तावेज ऑडिट करें (KagazCheck)",
                        ]
                    else:
                        suggested_followups = [
                            f"What documents do I need for {s_name.split('(')[0].strip()}?",
                            f"Where do I apply?",
                            f"Am I eligible for {s_name.split('(')[0].strip()}?",
                        ]

                # Add Action links
                action_links.append(
                    VaniActionLink(
                        label="Audit Documents with KagazCheck" if lang == "en" else ("ಕಾಗಜ್‌ಚೆಕ್‌ನಲ್ಲಿ ದಾಖಲೆ ಪರಿಶೀಲಿಸಿ" if lang == "kn" else "कागज़चेक में दस्तावेज जांचें"),
                        action_type="open_kagazcheck",
                        payload={"scheme_id": matched_scheme_id},
                    )
                )
                action_links.append(
                    VaniActionLink(
                        label="Official Portal" if lang == "en" else ("ಅಧಿಕೃತ ಪೋರ್ಟಲ್" if lang == "kn" else "आधिकारिक पोर्टल"),
                        action_type="open_url",
                        payload={"url": target_scheme.get("application_url") or target_scheme.get("official_source_url", "")},
                    )
                )

        # -------------------------------------------------------------
        # SCENARIO 2: General Scheme Discovery / Multiple Schemes Eligibility
        # -------------------------------------------------------------
        elif sub_intent == "eligibility" or any(w in query.lower() for w in ["which", "all", "schemes", "ಯಾವ", "ಎಲ್ಲಾ", "ಯೋಜನೆಗಳು", "कौन", "सभी"]):
            intent = "general_eligibility"
            if profile_obj:
                match_res = yojanamatch_service.match_citizen(profile_obj)
                eligible_matches = [r for r in match_res.results if r.eligible_status]
                matched_ids = [m.scheme_id for m in eligible_matches]
                matched_schemes = [s for s in VERIFIED_SCHEMES_SEED if s["id"] in matched_ids]
                scheme_cards = self._build_scheme_cards(matched_schemes, profile_obj)
                
                names_str = ", ".join([s["name"].split("(")[0].strip() for s in matched_schemes[:3]])
                if lang == "kn":
                    reply_text = (
                        f"ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಆಧಾರದ ಮೇಲೆ, ನೀವು **{len(matched_schemes)} ಪರಿಶೀಲಿತ ಯೋಜನೆಗಳಿಗೆ** ಅರ್ಹರಾಗಿದ್ದೀರಿ:\n"
                        f"• {names_str}.\n\n"
                        f"ಪ್ರತಿಯೊಂದು ಯೋಜನೆಗೆ ಅಗತ್ಯ ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಲು ಕೆಳಗಿನ ಕಾರ್ಡ್‌ಗಳನ್ನು ನೋಡಿ."
                    )
                elif lang == "hi":
                    reply_text = (
                        f"आपके प्रोफ़ाइल के अनुसार आप **{len(matched_schemes)} सत्यापित योजनाओं** के लिए पात्र हैं:\n"
                        f"• {names_str}।\n\n"
                        f"विस्तृत नियम और दस्तावेज देखने के लिए नीचे दिए गए कार्ड देखें।"
                    )
                else:
                    reply_text = (
                        f"Based on your citizen profile, you qualify for **{len(matched_schemes)} verified statutory schemes**:\n"
                        f"• {names_str}.\n\n"
                        f"Check the scheme cards below to view document requirements and apply."
                    )
            else:
                scheme_cards = self._build_scheme_cards(VERIFIED_SCHEMES_SEED[:3])
                if lang == "kn":
                    reply_text = (
                        "ಗ್ರಾಮಸೇತು AI ನಲ್ಲಿ ರೈತರು, ಮಹಿಳೆಯರು, ಗ್ರಾಮೀಣ ಕುಟುಂಬಗಳು ಮತ್ತು ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಹಲವು ಶಾಸನಬದ್ಧ ಯೋಜನೆಗಳು ಲಭ್ಯವಿವೆ "
                        "(PM-KISAN, ರೇಷನ್ ಕಾರ್ಡ್, PMAY-G, PM-JAY, ಇತ್ಯಾದಿ). "
                        "ನಿಖರವಾದ ಅರ್ಹತೆ ತಿಳಿಯಲು ನಿಮ್ಮ ವಯಸ್ಸು, ಕೃಷಿ ಭೂಮಿ, ಅಥವಾ ಆದಾಯದ ವಿವರಗಳನ್ನು ತಿಳಿಸಿ."
                    )
                elif lang == "hi":
                    reply_text = (
                        "ग्रामसेतु AI पर किसानों, महिलाओं, ग्रामीण परिवारों और छात्रों के लिए कई सरकारी योजनाएं उपलब्ध हैं "
                        "(जैसे पीएम किसान, राशन कार्ड, पीएम आवास, आयुष्मान भारत)। "
                        "सटीक पात्रता जानने के लिए अपनी उम्र, जमीन या आय का विवरण साझा करें।"
                    )
                else:
                    reply_text = (
                        "GramSetu AI covers central and state welfare initiatives for farmers, rural families, women, and students "
                        "(e.g. PM-KISAN, Ration Card, PMAY-G Housing, PM-JAY Health, Raitha Vidya Nidhi). "
                        "To evaluate exact eligibility, tell me your occupation, landholding, or income."
                    )
            
            sources = ["National Schemes Repository", "GramSetu Rule Engine"]
            suggested_followups = [
                "What documents do I need for PM-KISAN?",
                "I want to apply for ration card",
                "Am I eligible for PMAY-G housing?",
            ]

        # -------------------------------------------------------------
        # SCENARIO 3: General Document Inquiry without active scheme
        # -------------------------------------------------------------
        elif sub_intent == "documents":
            intent = "general_document_inquiry"
            scheme_cards = self._build_scheme_cards(VERIFIED_SCHEMES_SEED[:3], profile_obj)
            sources = ["KagazCheck Statutory Document Standards"]
            if lang == "kn":
                reply_text = (
                    "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಅರ್ಜಿಗಾಗಿ ಪ್ರಮುಖವಾಗಿ ಈ ಕೆಳಗಿನ ಶಾಸನಬದ್ಧ ದಾಖಲೆಗಳು ಅಗತ್ಯವಿರುತ್ತವೆ:\n\n"
                    "1. **ಆಧಾರ್ ಕಾರ್ಡ್** (ಕುಟುಂಬದ ಎಲ್ಲಾ ಸದಸ್ಯರ ಆಧಾರ್)\n"
                    "2. **ರೇಷನ್ ಕಾರ್ಡ್ / ಬಿಪಿಎಲ್ ಕಾರ್ಡ್** (ಆಹಾರ ಭದ್ರತೆ ಮತ್ತು ವಸತಿ ಯೋಜನೆಗಳಿಗೆ)\n"
                    "3. **ಆಧಾರ್ ಲಿಂಕ್ ಆದ ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್** (ನೇರ ಡಿಬಿಟಿ ಹಣ ಜಮೆಗಾಗಿ)\n"
                    "4. **ಜಮೀನಿನ ಪಹಣಿ / ಆರ್‌ಒಆರ್ (ROR)** (ಕೃಷಿ ಯೋಜನೆಗಳಿಗೆ)\n"
                    "5. **ಆದಾಯ ಪ್ರಮಾಣಪತ್ರ** (ತಹಶೀಲ್ದಾರ್ ನೀಡಿದ ಪ್ರಮಾಣಪತ್ರ)\n\n"
                    "ನಿಮ್ಮಲ್ಲಿರುವ ದಾಖಲೆಗಳನ್ನು ಕಾಗಜ್‌ಚೆಕ್ (KagazCheck) ನಲ್ಲಿ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಪರಿಶೀಲಿಸಬಹುದು."
                )
            elif lang == "hi":
                reply_text = (
                    "सरकारी योजनाओं के लिए मुख्य रूप से ये दस्तावेज आवश्यक होते हैं:\n\n"
                    "1. **आधार कार्ड** (परिवार के सभी सदस्यों का)\n"
                    "2. **राशन कार्ड / बीपीएल कार्ड** (खाद्य सुरक्षा व आवास हेतु)\n"
                    "3. **आधार-सीडेड बैंक पासबुक** (डीबीटी राशि प्राप्त करने हेतु)\n"
                    "4. **जमीन का खसरा / खतौनी / ROR** (कृषि योजनाओं हेतु)\n"
                    "5. **आय प्रमाण पत्र** (तहसीलदार द्वारा जारी)\n\n"
                    "आप अपने दस्तावेजों को कागज़चेक (KagazCheck) से जांच सकते हैं।"
                )
            else:
                reply_text = (
                    "Standard government welfare schemes require the following key statutory certificates:\n\n"
                    "1. **Aadhaar Card** (Valid 12-digit UIDAI identity for all members)\n"
                    "2. **Ration / BPL Card** (Proof of food security and economic category)\n"
                    "3. **Aadhaar-seeded Bank Account Passbook** (For direct DBT cash transfer)\n"
                    "4. **Land Ownership RoR / Khasra** (For agricultural benefits)\n"
                    "5. **Income Certificate** (Issued by Revenue Authority / Tahsildar)\n\n"
                    "You can photograph your documents with KagazCheck camera auditor to verify statutory validity."
                )
            action_links.append(
                VaniActionLink(
                    label="Open KagazCheck Auditor" if lang == "en" else ("ಕಾಗಜ್‌ಚೆಕ್ ತೆರೆಯಿರಿ" if lang == "kn" else "कागज़चेक खोलें"),
                    action_type="open_kagazcheck",
                    payload={},
                )
            )

        # -------------------------------------------------------------
        # SCENARIO 4: General Civic Greeting / Polite Help
        # -------------------------------------------------------------
        else:
            intent = "civic_greeting"
            scheme_cards = self._build_scheme_cards(VERIFIED_SCHEMES_SEED[:2], profile_obj)
            if lang == "kn":
                reply_text = (
                    "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಗ್ರಾಮಸೇತು ಧ್ವನಿ ಸಹಾಯಕ (Vani-Bot). "
                    "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಅರ್ಹತೆ, ದಾಖಲೆಗಳ ಮಾಹಿತಿ, ಮತ್ತು ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ವಿಧಾನವನ್ನು ನನ್ನಲ್ಲಿ ಕೇಳಬಹುದು. "
                    "ಉದಾಹರಣೆಗೆ: 'ರೇಷನ್ ಕಾರ್ಡ್ಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?' ಅಥವಾ 'ಪಿಎಂ ಕಿಸಾನ್ ದಾಖಲೆಗಳು ಯಾವುವು?' ಎಂದು ಕೇಳಿ."
                )
                suggested_followups = [
                    "ರೇಷನ್ ಕಾರ್ಡ್ಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?",
                    "ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
                    "ಪಿಎಂ ಆವಾಸ್ ಗ್ರಾಮೀಣ ಯೋಜನೆಯ ಹಣ ಎಷ್ಟು?",
                ]
            elif lang == "hi":
                reply_text = (
                    "नमस्ते! मैं ग्रामसेतु का वाणी-बॉट (Vani-Bot) हूँ। "
                    "आप मुझसे सरकारी योजनाओं की पात्रता, जरूरी दस्तावेज और आवेदन प्रक्रिया के बारे में बोलकर पूछ सकते हैं। "
                    "उदाहरण के लिए: 'राशन कार्ड कैसे बनवाएं?' या 'पीएम किसान के लिए क्या दस्तावेज चाहिए?' पूछें।"
                )
                suggested_followups = [
                    "राशन कार्ड कैसे बनवाएं?",
                    "पीएम किसान के लिए क्या दस्तावेज चाहिए?",
                    "आयुष्मान भारत 5 लाख का इलाज कैसे मिलता है?",
                ]
            else:
                reply_text = (
                    "Namaste! I am Vani-Bot, your GramSetu voice assistant. "
                    "You can ask me about government scheme eligibility rules, required application documents, and benefits. "
                    "For example, try asking: 'I want to apply for ration card' or 'What documents do I need for PM-KISAN?'"
                )
                suggested_followups = [
                    "I want to apply for ration card",
                    "What documents do I need for PM-KISAN?",
                    "Am I eligible for PMAY-G housing?",
                ]
            sources = ["GramSetu Civic Intelligence"]

        # Record bounded conversation turn in session history (max 10 items)
        if session_id not in self._session_history:
            self._session_history[session_id] = []
        
        self._session_history[session_id].append({
            "query": query,
            "reply": reply_text,
            "intent": intent,
            "scheme_id": matched_scheme_id,
            "language": lang,
        })
        if len(self._session_history[session_id]) > 10:
            self._session_history[session_id] = self._session_history[session_id][-10:]

        return VaniRespondResponse(
            session_id=session_id,
            query=query,
            language=lang,
            intent=intent,
            reply_text=reply_text,
            reply_audio_base64=None,
            scheme_cards=scheme_cards,
            action_links=action_links,
            sources=sources,
            suggested_followups=suggested_followups,
            context_scheme_id=matched_scheme_id,
        )

    def clear_session(self, session_id: str):
        """
        Clears session state and conversation context memory.
        """
        if session_id in self._session_history:
            del self._session_history[session_id]
        if session_id in self._session_scheme_context:
            del self._session_scheme_context[session_id]
        if session_id in self._session_language_context:
            del self._session_language_context[session_id]
        if session_id in self._session_intent_context:
            del self._session_intent_context[session_id]


conversation_service = VaniConversationService()

