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
    and localized linguistic response synthesis across Kannada, Hindi, and English.
    """

    def __init__(self):
        # Bounded in-memory multi-turn session cache
        self._session_history: Dict[str, List[Dict[str, Any]]] = {}
        self._session_scheme_context: Dict[str, str] = {}

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

    def respond(self, req: VaniRespondRequest) -> VaniRespondResponse:
        """
        Processes a conversational civic query turn, performs grounded reasoning, and returns response.
        """
        session_id = req.session_id or f"vani_sess_{uuid.uuid4().hex[:10]}"
        lang = language_service.normalize_language_code(req.language)
        query = self._redact_pii(req.query.strip())
        
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
        
        # Context resolution from previous turn in session or explicit context
        if not matched_scheme_id or matched_scheme_id not in valid_scheme_ids:
            if req.context_scheme_id and req.context_scheme_id in valid_scheme_ids:
                matched_scheme_id = req.context_scheme_id
            elif session_id in self._session_scheme_context:
                matched_scheme_id = self._session_scheme_context[session_id]

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

        # Check intent types
        q_low = query.lower()
        is_doc_query = any(w in q_low for w in ["document", "documents", "kagaz", "ದಾಖಲೆ", "ಪ್ರಮಾಣಪತ್ರ", "कागजात", "दस्तावेज", "passbook", "aadhaar", "ಆಧಾರ್", "आधार"])
        is_elig_query = any(w in q_low for w in ["eligible", "eligibility", "qualify", "ಅರ್ಹತೆ", "ಅರ್ಹನೆ", "पात्रता", "पात्र"])
        is_benefit_query = any(w in q_low for w in ["benefit", "benefits", "money", "grant", "ಪ್ರಯೋಜನ", "ಹಣ", "ಮೊತ್ತ", "लाभ", "पैसा", "राशि"])
        is_apply_query = any(w in q_low for w in ["apply", "where", "how", "process", "ಅರ್ಜಿ", "ಎಲ್ಲಿ", "ಹೇಗೆ", "आवेदन", "कहाँ", "कैसे"])
        is_next_step_query = any(w in q_low for w in ["next", "prepare", "missing", "ಮುಂದೆ", "ಸಿದ್ಧತೆ", "आगे", "तैयारी"])

        # -------------------------------------------------------------
        # SCENARIO 1: Specific Scheme Query (e.g. PM-KISAN, PMAY-G, etc.)
        # -------------------------------------------------------------
        if matched_scheme_id and matched_scheme_id in [s["id"] for s in VERIFIED_SCHEMES_SEED]:
            target_scheme = self._get_scheme_by_id(matched_scheme_id)
            if target_scheme:
                scheme_cards = self._build_scheme_cards([target_scheme], profile_obj)
                sources = [target_scheme.get("official_source_url", "Official Gazette")]

                s_name = target_scheme.get("name", "")
                benefits_str = ", ".join(target_scheme.get("benefits", [])[:2])
                docs_list = target_scheme.get("required_documents", [])
                docs_str = ", ".join(docs_list[:3])

                # Check eligibility if profile available
                elig_status_str = ""
                if profile_obj:
                    eval_res = yojanamatch_service.evaluate_scheme(target_scheme, profile_obj)
                    if eval_res.eligible_status:
                        elig_status_str = " (You are eligible based on your profile!)"
                    else:
                        elig_status_str = " (Check requirements to confirm eligibility.)"

                if is_doc_query:
                    intent = "document_inquiry"
                    if lang == "kn":
                        reply_text = (
                            f"**{s_name}** ಯೋಜನೆಗೆ ಅಗತ್ಯವಿರುವ ಮುಖ್ಯ ದಾಖಲೆಗಳು:\n"
                            + "\n".join([f"• {d}" for d in docs_list])
                            + f"\n\nಈ ದಾಖಲೆಗಳನ್ನು ನೀವು ಕಾಗಜ್‌ಚೆಕ್ (KagazCheck) ನಲ್ಲಿ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಪರಿಶೀಲಿಸಬಹುದು."
                        )
                        suggested_followups = [
                            f"ನನಗೆ {s_name} ಸಿಗುತ್ತದೆಯೇ?",
                            "ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಎಲ್ಲಿಗೆ ಹೋಗಬೇಕು?",
                            "ಯೋಜನೆಯ ಪ್ರಯೋಜನವೇನು?",
                        ]
                    elif lang == "hi":
                        reply_text = (
                            f"**{s_name}** के लिए आवश्यक प्रमुख दस्तावेज निम्नलिखित हैं:\n"
                            + "\n".join([f"• {d}" for d in docs_list])
                            + f"\n\nआप इन दस्तावेजों की शुद्धता कागज़चेक (KagazCheck) द्वारा सत्यापित कर सकते हैं।"
                        )
                        suggested_followups = [
                            f"क्या मैं {s_name} के लिए पात्र हूँ?",
                            "आवेदन कहाँ और कैसे करें?",
                            "इस योजना के लाभ क्या हैं?",
                        ]
                    else:
                        reply_text = (
                            f"For **{s_name}**, the required statutory documents are:\n"
                            + "\n".join([f"• {d}" for d in docs_list])
                            + f"\n\nYou can audit your certificates with KagazCheck before applying."
                        )
                        suggested_followups = [
                            f"Am I eligible for {s_name}?",
                            "Where do I apply?",
                            "What are the benefits?",
                        ]

                elif is_benefit_query:
                    intent = "benefit_inquiry"
                    if lang == "kn":
                        reply_text = (
                            f"**{s_name}** ಯೋಜನೆಯ ಮುಖ್ಯ ಪ್ರಯೋಜನಗಳು:\n"
                            + "\n".join([f"• {b}" for b in target_scheme.get("benefits", [])])
                        )
                        suggested_followups = [
                            f"{s_name} ಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
                            "ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?",
                        ]
                    elif lang == "hi":
                        reply_text = (
                            f"**{s_name}** के तहत मिलने वाले मुख्य लाभ:\n"
                            + "\n".join([f"• {b}" for b in target_scheme.get("benefits", [])])
                        )
                        suggested_followups = [
                            f"{s_name} के लिए दस्तावेज क्या हैं?",
                            "आवेदन कैसे करें?",
                        ]
                    else:
                        reply_text = (
                            f"Key benefits under **{s_name}**:\n"
                            + "\n".join([f"• {b}" for b in target_scheme.get("benefits", [])])
                        )
                        suggested_followups = [
                            f"What documents are required for {s_name}?",
                            "How do I apply?",
                        ]

                elif is_apply_query or is_next_step_query:
                    intent = "application_guidance"
                    app_url = target_scheme.get("application_url") or target_scheme.get("official_source_url")
                    if lang == "kn":
                        reply_text = (
                            f"**{s_name}** ಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ವಿಧಾನ:\n"
                            f"1. ಅಗತ್ಯ ದಾಖಲೆಗಳನ್ನು ಸಿದ್ಧಪಡಿಸಿಕೊಳ್ಳಿ ({docs_str}).\n"
                            f"2. ಹತ್ತಿರದ ಗ್ರಾಮ ಒನ್ (Gram One) / ಸಿಎಸ್‌ಸಿ ಕೇಂದ್ರ (CSC Kendra) ಅಥವಾ ಅಧಿಕೃತ ಪೋರ್ಟಲ್ ({app_url}) ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.\n"
                            f"3. ನಿಮ್ಮ ಆಧಾರ್ ಲಿಂಕ್ ಆಗಿರುವ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ನೇರ ಹಣ ಜಮೆಯಾಗುತ್ತದೆ."
                        )
                        suggested_followups = [
                            f"{s_name} ಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
                            "ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ (KagazCheck)",
                        ]
                    elif lang == "hi":
                        reply_text = (
                            f"**{s_name}** के लिए आवेदन कैसे करें:\n"
                            f"1. अपने आवश्यक दस्तावेज तैयार करें ({docs_str})।\n"
                            f"2. अपने नजदीकी जन सेवा केंद्र (CSC Kendra) या आधिकारिक पोर्टल ({app_url}) पर ऑनलाइन आवेदन करें।\n"
                            f"3. राशि सीधे आपके आधार लिंक बैंक खाते में भेजी जाएगी।"
                        )
                        suggested_followups = [
                            f"{s_name} के दस्तावेज क्या हैं?",
                            "दस्तावेज ऑडिट करें (KagazCheck)",
                        ]
                    else:
                        reply_text = (
                            f"How to apply for **{s_name}**:\n"
                            f"1. Prepare your statutory documents ({docs_str}).\n"
                            f"2. Submit at your nearest Common Service Centre (CSC) or on the official portal ({app_url}).\n"
                            f"3. Benefits will be directly transferred to your Aadhaar-seeded bank account."
                        )
                        suggested_followups = [
                            f"What documents do I need for {s_name}?",
                            "Audit documents with KagazCheck",
                        ]

                else:
                    # General Scheme summary
                    intent = "scheme_summary"
                    summary = target_scheme.get("detailed_description") or target_scheme.get("short_description")
                    if lang == "kn":
                        reply_text = (
                            f"**{s_name}** ವಿವರ:\n"
                            f"{summary}\n\n"
                            f"• **ಪ್ರಯೋಜನಗಳು**: {benefits_str}\n"
                            f"• **ಮುಖ್ಯ ದಾಖಲೆಗಳು**: {docs_str}{elig_status_str}"
                        )
                        suggested_followups = [
                            f"{s_name} ಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
                            f"ನನಗೆ {s_name} ಸಿಗುತ್ತದೆಯೇ?",
                            "ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?",
                        ]
                    elif lang == "hi":
                        reply_text = (
                            f"**{s_name}** विवरण:\n"
                            f"{summary}\n\n"
                            f"• **लाभ**: {benefits_str}\n"
                            f"• **आवश्यक दस्तावेज**: {docs_str}{elig_status_str}"
                        )
                        suggested_followups = [
                            f"{s_name} के लिए आवश्यक दस्तावेज?",
                            f"क्या मैं {s_name} के लिए पात्र हूँ?",
                            "आवेदन कहाँ करें?",
                        ]
                    else:
                        reply_text = (
                            f"**{s_name}** Summary:\n"
                            f"{summary}\n\n"
                            f"• **Benefits**: {benefits_str}\n"
                            f"• **Required Documents**: {docs_str}{elig_status_str}"
                        )
                        suggested_followups = [
                            f"What documents do I need for {s_name}?",
                            f"Am I eligible for {s_name}?",
                            "How do I apply?",
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
                        payload={"url": target_scheme.get("official_source_url", "")},
                    )
                )

        # -------------------------------------------------------------
        # SCENARIO 2: General Eligibility Query across multiple schemes
        # -------------------------------------------------------------
        elif is_elig_query or (profile_obj and any(w in q_low for w in ["which", "all", "ಯಾವ", "ಎಲ್ಲಾ", "कौन", "सभी"])):
            intent = "general_eligibility"
            evaluated = []
            if profile_obj:
                match_res = yojanamatch_service.match_citizen(profile_obj)
                eligible_matches = [r for r in match_res.results if r.eligible_status]
                matched_ids = [m.scheme_id for m in eligible_matches]
                matched_schemes = [s for s in VERIFIED_SCHEMES_SEED if s["id"] in matched_ids]
                scheme_cards = self._build_scheme_cards(matched_schemes, profile_obj)
                
                names_str = ", ".join([s["name"] for s in matched_schemes[:3]])
                if lang == "kn":
                    reply_text = (
                        f"ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಆಧಾರದ ಮೇಲೆ, ನೀವು **{len(matched_schemes)} ಯೋಜನೆಗಳಿಗೆ** ಅರ್ಹರಾಗಿದ್ದೀರಿ:\n"
                        f"{names_str}.\n\n"
                        f"ಪ್ರತಿಯೊಂದು ಯೋಜನೆಗೆ ಅಗತ್ಯ ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಲು ಕೆಳಗಿನ ಕಾರ್ಡ್‌ಗಳನ್ನು ನೋಡಿ."
                    )
                elif lang == "hi":
                    reply_text = (
                        f"आपके प्रोफ़ाइल के अनुसार आप **{len(matched_schemes)} योजनाओं** के लिए पात्र हैं:\n"
                        f"{names_str}।\n\n"
                        f"विस्तृत नियम और दस्तावेज देखने के लिए नीचे दिए गए कार्ड देखें।"
                    )
                else:
                    reply_text = (
                        f"Based on your citizen profile, you are eligible for **{len(matched_schemes)} statutory schemes**:\n"
                        f"{names_str}.\n\n"
                        f"Check the scheme cards below to view document requirements and apply."
                    )
            else:
                scheme_cards = self._build_scheme_cards(VERIFIED_SCHEMES_SEED[:3])
                if lang == "kn":
                    reply_text = (
                        "ಗ್ರಾಮಸೇತು AI ನಲ್ಲಿ ರೈತರು, ಮಹಿಳೆಯರು, ಗ್ರಾಮೀಣ ಕುಟುಂಬಗಳು ಮತ್ತು ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಹಲವು ಯೋಜನೆಗಳು ಲಭ್ಯವಿವೆ (PM-KISAN, PMAY-G, PM-JAY, ಇತ್ಯಾದಿ). "
                        "ನಿಖರವಾದ ಅರ್ಹತೆ ತಿಳಿಯಲು ನಿಮ್ಮ ವಯಸ್ಸು, ಕೃಷಿ ಭೂಮಿ, ಅಥವಾ ಆದಾಯದ ವಿವರಗಳನ್ನು ತಿಳಿಸಿ."
                    )
                elif lang == "hi":
                    reply_text = (
                        "ग्रामसेतु AI पर किसानों, महिलाओं, ग्रामीण परिवारों और छात्रों के लिए कई सरकारी योजनाएं उपलब्ध हैं (जैसे पीएम किसान, पीएम आवास, आयुष्मान भारत)। "
                        "सटीक पात्रता जानने के लिए अपनी उम्र, जमीन या आय का विवरण साझा करें।"
                    )
                else:
                    reply_text = (
                        "GramSetu AI covers central and state welfare initiatives for farmers, rural families, women, and students (e.g. PM-KISAN, PMAY-G, PM-JAY, Raitha Vidya Nidhi). "
                        "To evaluate exact eligibility, tell me your occupation, landholding, or state."
                    )
            
            sources = ["National Schemes Repository", "GramSetu Rule Engine"]
            suggested_followups = [
                "What documents do I need for PM-KISAN?",
                "Am I eligible for PMAY-G?",
                "How do I apply for health insurance?",
            ]

        # -------------------------------------------------------------
        # SCENARIO 3: General Greeting / Civic Help
        # -------------------------------------------------------------
        else:
            intent = "civic_greeting"
            scheme_cards = self._build_scheme_cards(VERIFIED_SCHEMES_SEED[:2], profile_obj)
            if lang == "kn":
                reply_text = (
                    "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಗ್ರಾಮಸೇತು ಧ್ವನಿ ಸಹಾಯಕ (Vani-Bot). "
                    "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಅರ್ಹತೆ, ದಾಖಲೆಗಳ ಮಾಹಿತಿ, ಮತ್ತು ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ವಿಧಾನವನ್ನು ನನ್ನಲ್ಲಿ ಕೇಳಬಹುದು. "
                    "ಉದಾಹರಣೆಗೆ: 'ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?' ಎಂದು ಕೇಳಿ."
                )
                suggested_followups = [
                    "ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
                    "ಪಿಎಂ ಆವಾಸ್ ಗ್ರಾಮೀಣ ಯೋಜನೆಯ ಹಣ ಎಷ್ಟು?",
                    "ನನಗೆ ಯಾವ ಯೋಜನೆ ಸಿಗುತ್ತದೆ?",
                ]
            elif lang == "hi":
                reply_text = (
                    "नमस्ते! मैं ग्रामसेतु का वाणी-बॉट (Vani-Bot) हूँ। "
                    "आप मुझसे सरकारी योजनाओं की पात्रता, जरूरी दस्तावेज और आवेदन प्रक्रिया के बारे में बोलकर पूछ सकते हैं। "
                    "उदाहरण के लिए: 'पीएम किसान के लिए क्या दस्तावेज चाहिए?' पूछें।"
                )
                suggested_followups = [
                    "पीएम किसान के लिए क्या दस्तावेज चाहिए?",
                    "पीएम आवास योजना ग्रामीण में कितना पैसा मिलता है?",
                    "आयुष्मान भारत 5 लाख का इलाज कैसे मिलता है?",
                ]
            else:
                reply_text = (
                    "Namaste! I am Vani-Bot, your GramSetu voice assistant. "
                    "You can ask me about government scheme eligibility rules, required application documents, and benefits. "
                    "For example, try asking: 'What documents do I need for PM-KISAN?'"
                )
                suggested_followups = [
                    "What documents do I need for PM-KISAN?",
                    "Am I eligible for PMAY-G housing?",
                    "What health benefits does PM-JAY offer?",
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


conversation_service = VaniConversationService()
