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

    def converse(self, req: VaniConverseRequest) -> VaniConverseResponse:
        """
        Processes a voice/text turn, performs grounded scheme reasoning, and returns response in requested language.
        """
        session_id = req.session_id or f"vani_sess_{uuid.uuid4().hex[:10]}"
        lang = language_service.normalize_language_code(req.language)
        query = req.user_query.strip()
        
        # Build CitizenProfile object if profile dict passed
        profile_obj: Optional[CitizenProfile] = None
        if req.citizen_profile:
            try:
                profile_obj = CitizenProfile(**req.citizen_profile)
            except Exception as e:
                logger.warning(f"Could not parse citizen profile in Vani-Bot: {e}")

        # Detect intent and scheme association
        matched_scheme_id, confidence = language_service.detect_scheme_intent(query)
        if req.context_scheme_id and not matched_scheme_id:
            matched_scheme_id = req.context_scheme_id

        # Response construction components
        reply_text = ""
        scheme_cards: List[VaniSchemeCard] = []
        action_links: List[VaniActionLink] = []
        sources: List[str] = []
        suggested_followups: List[str] = []

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
                elig_note_kn = ""
                elig_note_hi = ""
                elig_note_en = ""
                if profile_obj:
                    eval_res = yojanamatch_service.evaluate_scheme(target_scheme, profile_obj)
                    if eval_res.eligible_status:
                        elig_note_kn = "ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಪರಿಶೀಲಿಸಲಾಗಿದ್ದು, ನೀವು ಈ ಯೋಜನೆಗೆ 100% ಅರ್ಹರಾಗಿದ್ದೀರಿ."
                        elig_note_hi = "आपकी प्रोफाइल के आधार पर आप इस योजना के लिए 100% पात्र हैं।"
                        elig_note_en = "Based on your profile, you are 100% eligible for this scheme."
                    else:
                        failed_reasons = [r.description for r in eval_res.failed_rules if r.description]
                        reason = failed_reasons[0] if failed_reasons else "ಮಾನದಂಡಗಳು ಹೊಂದುತ್ತಿಲ್ಲ"
                        elig_note_kn = f"ಗಮನಿಸಿ: ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಪ್ರಕಾರ ({reason})."
                        elig_note_hi = f"ध्यान दें: आपकी प्रोफाइल के अनुसार ({reason})।"
                        elig_note_en = f"Note: Rule criteria not fully met ({reason})."

                # Localized Grounded Explanations
                if lang == "kn":
                    if matched_scheme_id == "pm-kisan-001":
                        reply_text = (
                            f"**ಪಿಎಂ ಕಿಸಾನ್ (PM-KISAN)** ಯೋಜನೆಯಡಿ ಜಮೀನು ಹೊಂದಿರುವ ರೈತ ಕುಟುಂಬಗಳಿಗೆ ವರ್ಷಕ್ಕೆ ₹6,000 "
                            f"(ಪ್ರತಿ 4 ತಿಂಗಳಿಗೊಮ್ಮೆ ₹2,000) ನೇರವಾಗಿ ಬ್ಯಾಂಕ್ ಖಾತೆಗೆ ಜಮೆಯಾಗುತ್ತದೆ. "
                            f"{elig_note_kn}\n\n"
                            f"**ಅಗತ್ಯ ದಾಖಲೆಗಳು:** {docs_str}.\n"
                            f"ದಾಖಲೆಗಳನ್ನು ಕಾಗಜ್‌ಚೆಕ್ (KagazCheck) ಕ್ಯಾಮೆರಾ ಮೂಲಕ ಪರಿಶೀಲಿಸಲು ಕೆಳಗಿನ ಬಟನ್ ಒತ್ತಿರಿ."
                        )
                    elif matched_scheme_id == "pmay-g-002":
                        reply_text = (
                            f"**ಪ್ರಧಾನ ಮಂತ್ರಿ ಆವಾಸ್ ಯೋಜನೆ - ಗ್ರಾಮೀಣ (PMAY-G)** ಅಡಿಯಲ್ಲಿ ಪಕ್ಕಾ ಮನೆ ನಿರ್ಮಿಸಲು "
                            f"₹1,20,000 ಆರ್ಥಿಕ ಅನುದಾನ ಹಾಗೂ ನರೇಗಾ (MGNREGA) ಅಡಿಯಲ್ಲಿ ಕೂಲಿ ಹಣ ಸಿಗುತ್ತದೆ. "
                            f"{elig_note_kn}\n\n"
                            f"**ಅಗತ್ಯ ದಾಖಲೆಗಳು:** {docs_str}."
                        )
                    elif matched_scheme_id == "raitha-vidya-005":
                        reply_text = (
                            f"**ಕರ್ನಾಟಕ ರೈತ ವಿದ್ಯಾನಿಧಿ** ಯೋಜನೆಯು ರೈತರ ಮಕ್ಕಳಿಗೆ ಪಿಯುಸಿ, ಐಟಿಐ, ಡಿಗ್ರಿ ಮತ್ತು ಸ್ನಾತಕೋತ್ತರ "
                            f"ಶಿಕ್ಷಣಕ್ಕಾಗಿ ₹2,000 ರಿಂದ ₹11,000 ವರೆಗೆ ವಾರ್ಷಿಕ ವಿದ್ಯಾರ್ಥಿವೇತನ ನೀಡುತ್ತದೆ. "
                            f"{elig_note_kn}\n\n"
                            f"**ಅಗತ್ಯ ದಾಖಲೆಗಳು:** {docs_str}."
                        )
                    elif matched_scheme_id == "pm-jay-004":
                        reply_text = (
                            f"**ಆಯುಷ್ಮಾನ್ ಭಾರತ್ (PM-JAY)** ಅಡಿಯಲ್ಲಿ ಅರ್ಹ ಬಡ ಕುಟುಂಬಗಳಿಗೆ ಪ್ರತಿ ವರ್ಷ ₹5,00,000 ವರೆಗೆ "
                            f"ಉಚಿತ ನಗದುರಹಿತ ಆಸ್ಪತ್ರೆ ಚಿಕಿತ್ಸೆ ಸೌಲಭ್ಯ ದೊರೆಯುತ್ತದೆ. {elig_note_kn}"
                        )
                    else:
                        reply_text = (
                            f"**{s_name}** ಕುರಿತು ವಿವರ: {target_scheme.get('short_description', '')}. "
                            f"ಪ್ರಯೋಜನಗಳು: {benefits_str}. {elig_note_kn}\n"
                            f"ಅಗತ್ಯ ದಾಖಲೆಗಳು: {docs_str}."
                        )

                    suggested_followups = [
                        f"{s_name} ಗೆ ದಾಖಲೆ ಪರಿಶೀಲಿಸಿ",
                        "ನನ್ನ ಅರ್ಹತೆ ಇನ್ನೊಮ್ಮೆ ನೋಡಿ",
                        "ಇತರ ಯೋಜನೆಗಳನ್ನು ತಿಳಿಸಿ",
                    ]

                elif lang == "hi":
                    if matched_scheme_id == "pm-kisan-001":
                        reply_text = (
                            f"**पीएम किसान सम्मान निधि** योजना के तहत पात्र किसान परिवारों को प्रति वर्ष ₹6,000 "
                            f"(₹2,000 की 3 किस्तों में) सीधे आधार-सीडेड बैंक खाते में दिए जाते हैं। "
                            f"{elig_note_hi}\n\n"
                            f"**आवश्यक दस्तावेज:** {docs_str}।\n"
                            f"दस्तावेजों को कागज़चेक (KagazCheck) कैमरे से जांचने के लिए नीचे दिए गए बटन पर क्लिक करें।"
                        )
                    elif matched_scheme_id == "pmay-g-002":
                        reply_text = (
                            f"**प्रधानमंत्री आवास योजना - ग्रामीण (PMAY-G)** के तहत बेघर और कच्चे मकान वाले परिवारों को "
                            f"पक्का मकान बनाने के लिए ₹1,20,000 की वित्तीय सहायता दी जाती है। "
                            f"{elig_note_hi}\n\n"
                            f"**आवश्यक दस्तावेज:** {docs_str}।"
                        )
                    elif matched_scheme_id == "pm-jay-004":
                        reply_text = (
                            f"**आयुष्मान भारत (PM-JAY)** योजना के तहत पात्र परिवारों को प्रति वर्ष ₹5,00,000 तक का "
                            f"निःशुल्क कैशलेस स्वास्थ्य बीमा कवर मिलता है। {elig_note_hi}"
                        )
                    else:
                        reply_text = (
                            f"**{s_name}** का विवरण: {target_scheme.get('short_description', '')}। "
                            f"लाभ: {benefits_str}। {elig_note_hi}\n"
                            f"आवश्यक दस्तावेज: {docs_str}।"
                        )

                    suggested_followups = [
                        f"{s_name} के दस्तावेज जांचें",
                        "मेरी पात्रता चेक करें",
                        "अन्य सरकारी योजनाएं बताएं",
                    ]

                else:  # English
                    reply_text = (
                        f"Under **{s_name}**, eligible citizens receive key statutory entitlements: {benefits_str}. "
                        f"{elig_note_en}\n\n"
                        f"**Required Documents:** {docs_str}.\n"
                        f"You can verify your documents using KagazCheck camera auditor below."
                    )
                    suggested_followups = [
                        f"Audit documents for {s_name}",
                        "Check my full eligibility",
                        "Show all agricultural schemes",
                    ]

                # Add Action Links
                action_links.append(
                    VaniActionLink(
                        label="Audit Documents on KagazCheck" if lang == "en" else ("ಕಾಗಜ್‌ಚೆಕ್‌ನಲ್ಲಿ ದಾಖಲೆ ಪರಿಶೀಲಿಸಿ" if lang == "kn" else "कागज़चेक में दस्तावेज जांचें"),
                        action_type="open_kagazcheck",
                        payload={"scheme_id": matched_scheme_id},
                    )
                )

        # -------------------------------------------------------------
        # SCENARIO 2: General Eligibility Query (e.g. "What schemes for me?")
        # -------------------------------------------------------------
        elif matched_scheme_id == "general_eligibility" or any(w in query.lower() for w in ["which", "eligible", "qualify", "ಯಾವ", "ಸಿಗುತ್ತದೆ", "पात्र"]):
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
                        f"ನಮಸ್ಕಾರ! ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ({profile_obj.occupation or 'ರೈತ'}, {profile_obj.state or 'ಕರ್ನಾಟಕ'}, "
                        f"{profile_obj.landholding or 2.5} ಎಕರೆ ಜಮೀನು) ಪರಿಶೀಲಿಸಲಾಗಿದ್ದು, ನೀವು **{len(eligible_schemes)} ಯೋಜನೆಗಳಿಗೆ** ಅರ್ಹರಾಗಿದ್ದೀರಿ:\n\n"
                        f"• {s_names_kn}.\n\n"
                        f"ಯೋಜನೆಯ ವಿವರ ಹಾಗೂ ಕಾಗಜ್‌ಚೆಕ್ ಮೂಲಕ ದಾಖಲೆ ಪರಿಶೀಲನೆ ಮಾಡಲು ಕೆಳಗಿನ ಕಾರ್ಡ್‌ಗಳನ್ನು ನೋಡಿ."
                    )
                    suggested_followups = ["ಪಿಎಂ ಕಿಸಾನ್ ಬಗ್ಗೆ ತಿಳಿಸಿ", "ದಾಖಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ", "ವಿದ್ಯಾನಿಧಿ ಅರ್ಜಿ ಹೇಗೆ?"]
                elif lang == "hi":
                    reply_text = (
                        f"नमस्ते! आपकी प्रोफाइल ({profile_obj.occupation or 'किसान'}, {profile_obj.state or 'कर्नाटक'}, "
                        f"{profile_obj.landholding or 2.5} एकड़ जमीन) के आधार पर आप **{len(eligible_schemes)} योजनाओं** के लिए पात्र हैं:\n\n"
                        f"• {s_names_hi}।\n\n"
                        f"विस्तृत जानकारी और कागज़ात जांच के लिए नीचे दिए गए कार्ड्स देखें।"
                    )
                    suggested_followups = ["पीएम किसान की जानकारी", "कागजात की जांच करें", "आवास योजना के नियम"]
                else:
                    reply_text = (
                        f"Based on your profile ({profile_obj.occupation or 'Farmer'}, {profile_obj.state or 'Karnataka'}, "
                        f"{profile_obj.landholding or 2.5} acres land), you qualify for **{len(eligible_schemes)} verified schemes**:\n\n"
                        f"• {s_names_en}.\n\n"
                        f"Check the cards below for benefits, eligibility rules, and document verification."
                    )
                    suggested_followups = ["Explain PM-KISAN rules", "Audit my documents", "How to apply?"]
            else:
                # Default popular schemes
                top_schemes = VERIFIED_SCHEMES_SEED[:3]
                scheme_cards = self._build_scheme_cards(top_schemes)
                sources = ["GramSetu Schemes Repository"]

                if lang == "kn":
                    reply_text = (
                        "ಗ್ರಾಮಸೇತು ಎಐ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಪ್ರಮುಖವಾಗಿ ಪಿಎಂ ಕಿಸಾನ್, ಪಿಎಂ ಆವಾಸ್ ಗ್ರಾಮೀಣ, ಆಯುಷ್ಮಾನ್ ಭಾರತ್ ಮತ್ತು ರೈತ ವಿದ್ಯಾನಿಧಿ "
                        "ಯೋಜನೆಗಳು ಲಭ್ಯವಿವೆ. ನಿಮ್ಮ ನಿರ್ದಿಷ್ಟ ಅರ್ಹತೆ ತಿಳಿಯಲು ಪ್ರೊಫೈಲ್ ವಿವರ ನಮೂದಿಸಿ."
                    )
                elif lang == "hi":
                    reply_text = (
                        "ग्रामसेतु एआई पर प्रमुख योजनाएं जैसे पीएम किसान, पीएम आवास ग्रामीण, आयुष्मान भारत और मातृ वंदना उपलब्ध हैं। "
                        "अपनी पात्रता जांचने के लिए प्रोफाइल विवरण दर्ज करें।"
                    )
                else:
                    reply_text = (
                        "GramSetu AI features verified statutory welfare schemes including PM-KISAN, PMAY-G, PM-JAY, and Raitha Vidya Nidhi. "
                        "Fill in your profile parameters to evaluate deterministic eligibility."
                    )

            action_links.append(
                VaniActionLink(
                    label="Find All Eligible Schemes" if lang == "en" else ("ಅರ್ಹ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಿ" if lang == "kn" else "पात्र योजनाएं खोजें"),
                    action_type="check_eligibility",
                    payload={},
                )
            )

        # -------------------------------------------------------------
        # SCENARIO 3: Document Inquiry (e.g. "What documents needed?")
        # -------------------------------------------------------------
        elif matched_scheme_id == "document_inquiry" or any(w in query.lower() for w in ["document", "kagaz", "ದಾಖಲೆ", "दस्तावेज", "aadhaar", "ಆಧಾರ್"]):
            all_docs_schemes = VERIFIED_SCHEMES_SEED[:2]
            scheme_cards = self._build_scheme_cards(all_docs_schemes, profile_obj)
            sources = ["KagazCheck Statutory Document Standards"]

            if lang == "kn":
                reply_text = (
                    "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳಿಗೆ ಮುಖ್ಯವಾಗಿ ಈ ಕೆಳಗಿನ ದಾಖಲೆಗಳು ಅಗತ್ಯವಿರುತ್ತವೆ:\n\n"
                    "1. **ಆಧಾರ್ ಕಾರ್ಡ್** (12 ಅಂಕೆಗಳು, ಹೆಸರು ಸ್ಪಷ್ಟವಿರಬೇಕು)\n"
                    "2. **ಜಮೀನಿನ ಪಹಣಿ / ಆರ್‌ಒಆರ್ (ROR)** (ಕೃಷಿ ಯೋಜನೆಗಳಿಗೆ)\n"
                    "3. **ಆಧಾರ್ ಲಿಂಕ್ ಆದ ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್** (ಡಿಬಿಟಿ ಜಮೆಗಾಗಿ)\n"
                    "4. **ರೇಷನ್ ಕಾರ್ಡ್ / ಬಿಪಿಎಲ್ ಕಾರ್ಡ್**\n\n"
                    "ನಿಮ್ಮಲ್ಲಿರುವ ದಾಖಲೆಗಳನ್ನು ಕಾಗಜ್‌ಚೆಕ್ (KagazCheck) ಕ್ಯಾಮೆರಾ ಮೂಲಕ ಫೋಟೋ ತೆಗೆದು ತಕ್ಷಣ ಪರಿಶೀಲಿಸಬಹುದು."
                )
            elif lang == "hi":
                reply_text = (
                    "सरकारी योजनाओं के आवेदन के लिए मुख्य रूप से ये दस्तावेज आवश्यक हैं:\n\n"
                    "1. **आधार कार्ड** (12 अंकों का वैध आधार)\n"
                    "2. **जमीन का खसरा / खतौनी / ROR** (कृषि योजनाओं के लिए)\n"
                    "3. **आधार-सीडेड बैंक पासबुक** (डीबीटी राशि प्राप्त करने हेतु)\n"
                    "4. **राशन कार्ड / बीपीएल कार्ड**\n\n"
                    "आप अपने दस्तावेजों को कागज़चेक (KagazCheck) कैमरे से स्कैन करके जांच सकते हैं।"
                )
            else:
                reply_text = (
                    "Standard government welfare schemes require the following key statutory certificates:\n\n"
                    "1. **Aadhaar Card** (Valid 12-digit UIDAI identity)\n"
                    "2. **Land Ownership RoR / Khasra** (For agricultural benefits)\n"
                    "3. **Aadhaar-seeded Bank Account Passbook** (For direct DBT cash transfer)\n"
                    "4. **Ration / BPL Card** (For rural welfare schemes)\n\n"
                    "You can photograph your documents with KagazCheck camera auditor to verify statutory validity."
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
                    "ನಾನು ಸರಕಾರಿ ಯೋಜನೆಗಳು, ಅರ್ಹತಾ ನಿಯಮಗಳು, ಹಾಗೂ ಕಾಗಜ್‌ಚೆಕ್ ಮೂಲಕ ದಾಖಲೆ ಪರಿಶೀಲನೆಗೆ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ. "
                    "ನೀವು ಕಿಸಾನ್ ಯೋಜನೆ, ಆವಾಸ್ ಯೋಜನೆ, ಅಥವಾ ವಿದ್ಯಾನಿಧಿ ಕುರಿತು ಧ್ವನಿಯಲ್ಲೇ ಕೇಳಬಹುದು."
                )
                suggested_followups = [
                    "ನನಗೆ ಯಾವ ಯೋಜನೆ ಸಿಗುತ್ತದೆ?",
                    "ಪಿಎಂ ಕಿಸಾನ್ ದಾಖಲೆಗಳು ಯಾವುವು?",
                    "ರೈತ ವಿದ್ಯಾನಿಧಿ ಮಾಹಿತಿ ತಿಳಿಸಿ",
                ]
            elif lang == "hi":
                reply_text = (
                    "नमस्ते! मैं आपका ग्रामसेतु वाणी सहायक (Vani-Bot) हूँ। "
                    "मैं सरकारी योजनाओं की पात्रता, आवश्यक दस्तावेजों और कागज़चेक सत्यापन में सहायता करता हूँ। "
                    "आप किसान योजना, आवास योजना या आयुष्मान भारत के बारे में सीधे बोलकर पूछ सकते हैं।"
                )
                suggested_followups = [
                    "मेरी पात्र योजनाएं बताएं",
                    "पीएम किसान के दस्तावेज",
                    "आयुष्मान भारत के लाभ",
                ]
            else:
                reply_text = (
                    "Namaste! I am your GramSetu Vani Voice Assistant. "
                    "I can help you discover statutory government schemes, verify eligibility criteria, and audit required documents with KagazCheck. "
                    "You can ask about PM-KISAN, PMAY-G Housing, PM-JAY Health, or state scholarships."
                )
                suggested_followups = [
                    "Which schemes am I eligible for?",
                    "What documents are needed for PM-KISAN?",
                    "Tell me about Raitha Vidya Nidhi",
                ]

        # Record in session history
        turn_data = {
            "query": query,
            "reply": reply_text,
            "language": lang,
        }
        if session_id not in self._session_history:
            self._session_history[session_id] = []
        self._session_history[session_id].append(turn_data)
        # Keep last 10 turns
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


conversation_service = VaniConversationService()
