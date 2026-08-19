import re
from typing import List, Dict, Any, Tuple, Optional
from app.schemas.vanibot import VaniLanguageInfo

SUPPORTED_LANGUAGES: List[VaniLanguageInfo] = [
    VaniLanguageInfo(
        code="kn",
        locale="kn-IN",
        name="Kannada",
        native_name="ಕನ್ನಡ",
        supported_for_stt=True,
        supported_for_tts=True,
        sample_queries=[
            "ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
            "ನನಗೆ 2.5 ಎಕರೆ ಜಮೀನಿದೆ, ಯಾವ ಯೋಜನೆ ಸಿಗುತ್ತದೆ?",
            "ಪಿಎಂ ಆವಾಸ್ ಗ್ರಾಮೀಣ ಯೋಜನೆಯ ಹಣ ಎಷ್ಟು?",
            "ಕರ್ನಾಟಕ ರೈತ ವಿದ್ಯಾನಿಧಿ ಸ್ಕಾಲರ್‌ಶಿಪ್ ಹೇಗೆ ಪಡೆಯುವುದು?",
            "ಆಯುಷ್ಮಾನ್ ಭಾರತ್ ಆರೋಗ್ಯ ಕಾರ್ಡ್ ಪ್ರಯೋಜನಗಳೇನು?",
        ],
    ),
    VaniLanguageInfo(
        code="hi",
        locale="hi-IN",
        name="Hindi",
        native_name="हिन्दी",
        supported_for_stt=True,
        supported_for_tts=True,
        sample_queries=[
            "पीएम किसान सम्मान निधि के लिए क्या पात्रता है?",
            "पीएम किसान के लिए कौन से दस्तावेज चाहिए?",
            "पीएम आवास योजना ग्रामीण में कितना पैसा मिलता है?",
            "मातृ वंदना योजना के लिए कौन से दस्तावेज चाहिए?",
            "आयुष्मान भारत 5 लाख का इलाज कैसे मिलता है?",
        ],
    ),
    VaniLanguageInfo(
        code="en",
        locale="en-IN",
        name="English",
        native_name="English",
        supported_for_stt=True,
        supported_for_tts=True,
        sample_queries=[
            "What documents do I need for PM-KISAN?",
            "Am I eligible for PMAY-G?",
            "How much financial grant does PMAY-G provide?",
            "What health benefits does PM-JAY offer?",
            "Am I eligible for Raitha Vidya Nidhi in Karnataka?",
        ],
    ),
    VaniLanguageInfo(
        code="te",
        locale="te-IN",
        name="Telugu",
        native_name="తెలుగు",
        supported_for_stt=True,
        supported_for_tts=True,
        sample_queries=[
            "పీఎం కిసాన్ పథకానికి ఏయే పత్రాలు కావాలి?",
            "ఆయుష్ಮಾన్ భారత్ ద్వారా ఎంత బీమా లభిస్తుంది?",
        ],
    ),
    VaniLanguageInfo(
        code="ta",
        locale="ta-IN",
        name="Tamil",
        native_name="தமிழ்",
        supported_for_stt=True,
        supported_for_tts=True,
        sample_queries=[
            "பிஎம் கிசான் திட்டத்திற்கு என்ன ஆவணங்கள் தேவை?",
            "ஆயுஷ்மான் பாரத் மருத்துவ காப்பீடு பலன்கள் என்ன?",
        ],
    ),
    VaniLanguageInfo(
        code="mr",
        locale="mr-IN",
        name="Marathi",
        native_name="मराठी",
        supported_for_stt=True,
        supported_for_tts=True,
        sample_queries=[
            "पीएम किसान योजनेसाठी कोणती कागदपत्रे लागतील?",
            "आयुष्मान भारत योजनेचे काय फायदे आहेत?",
        ],
    ),
]

from app.data.verified_schemes import VERIFIED_SCHEMES_SEED


class VaniLanguageService:
    """
    Multilingual intent and translation normalization service for regional Indian languages.
    Dynamically indexes schemes from verified database / seed architecture without requiring
    scheme-specific hardcoded mappings.
    """

    @classmethod
    def get_supported_languages(cls) -> List[VaniLanguageInfo]:
        return SUPPORTED_LANGUAGES

    @classmethod
    def normalize_language_code(cls, lang: Optional[str]) -> str:
        """
        Normalizes language code (e.g. 'kn-IN' -> 'kn', 'hi-IN' -> 'hi', 'en-US' -> 'en').
        Defaults to 'kn' for Karnataka GramSetu context if unspecified or unsupported.
        """
        if not lang or not isinstance(lang, str):
            return "kn"
        clean = lang.strip().lower()
        if clean.startswith("kn"):
            return "kn"
        elif clean.startswith("hi"):
            return "hi"
        elif clean.startswith("en"):
            return "en"
        elif clean.startswith("te"):
            return "te"
        elif clean.startswith("ta"):
            return "ta"
        elif clean.startswith("mr"):
            return "mr"
        return "kn"

    @classmethod
    def detect_language_from_text(cls, text: Optional[str], default_lang: str = "en") -> str:
        """
        Auto-detects language based on Unicode script ranges.
        """
        if not text or not isinstance(text, str):
            return cls.normalize_language_code(default_lang)
        
        # Kannada Unicode block: \u0C80-\u0CFF
        if re.search(r"[\u0C80-\u0CFF]", text):
            return "kn"
        # Devanagari (Hindi/Marathi) Unicode block: \u0900-\u097F
        elif re.search(r"[\u0900-\u097F]", text):
            return "hi"
        # Telugu Unicode block: \u0C00-\u0C7F
        elif re.search(r"[\u0C00-\u0C7F]", text):
            return "te"
        # Tamil Unicode block: \u0B80-\u0BFF
        elif re.search(r"[\u0B80-\u0BFF]", text):
            return "ta"
        
        return cls.normalize_language_code(default_lang)

    @classmethod
    def get_locale_for_language(cls, lang_code: str) -> str:
        code = cls.normalize_language_code(lang_code)
        match = next((l for l in SUPPORTED_LANGUAGES if l.code == code), None)
        return match.locale if match else "kn-IN"

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        Normalizes text by lowercasing, stripping extra whitespace, and standardizing punctuation.
        """
        if not text:
            return ""
        cleaned = text.lower().strip()
        cleaned = re.sub(r"[^\w\s\u0C80-\u0CFF\u0900-\u097F\u0C00-\u0C7F\u0B80-\u0BFF-]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def build_dynamic_scheme_index(cls, schemes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, List[str]]:
        """
        Dynamically extracts and indexes search keywords, aliases, acronyms, and localized names
        for any scheme present in the provided scheme catalog (defaults to VERIFIED_SCHEMES_SEED).
        Allows dynamic extensibility for any scheme without modifying Python code.
        """
        if schemes is None:
            schemes = VERIFIED_SCHEMES_SEED

        index: Dict[str, List[str]] = {}
        for s in schemes:
            s_id = s.get("id", "")
            if not s_id:
                continue
            
            keywords = set()
            # 1. Scheme ID tokens (e.g. "pm-kisan-001" -> "pm-kisan-001", "pm-kisan", "pmkisan")
            keywords.add(s_id)
            clean_id = re.sub(r'-\d+$', '', s_id)
            keywords.add(clean_id)
            keywords.add(clean_id.replace('-', ''))

            # 2. Scheme Name tokens & parentheses acronyms
            name = s.get("name", "")
            if name:
                keywords.add(name)
                # Extract acronyms inside parentheses e.g. "(PM-KISAN)", "(NFSA)"
                parentheses_matches = re.findall(r'\((.*?)\)', name)
                for m in parentheses_matches:
                    for part in m.split('/'):
                        p_clean = part.strip()
                        if p_clean:
                            keywords.add(p_clean)
                            keywords.add(p_clean.replace('-', ''))
                            keywords.add(p_clean.replace(' ', ''))

                # Clean name without parentheses
                clean_name = re.sub(r'\(.*?\)', '', name).strip()
                if clean_name:
                    keywords.add(clean_name)
                    for part in clean_name.split(' - '):
                        if len(part.strip()) > 3:
                            keywords.add(part.strip())

            # 3. Explicit Aliases defined in data
            for alias in s.get("aliases", []):
                if alias:
                    keywords.add(alias)

            # 4. Localized names defined in data
            for loc_name in s.get("localized_names", {}).values():
                if loc_name:
                    keywords.add(loc_name)
                    for m in re.findall(r'\((.*?)\)', loc_name):
                        for part in m.split('/'):
                            p_clean = part.strip()
                            if p_clean:
                                keywords.add(p_clean)
                    clean_loc = re.sub(r'\(.*?\)', '', loc_name).strip()
                    if clean_loc:
                        keywords.add(clean_loc)

            # Sort keywords by length descending so longer/more specific phrases match first
            index[s_id] = sorted(list(keywords), key=lambda x: len(x), reverse=True)

        return index

    @classmethod
    def detect_scheme_intent(
        cls,
        query: str,
        schemes: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[Optional[str], float]:
        """
        Identifies if user query relates to a specific verified government scheme across English, Kannada, Hindi, etc.
        Dynamically evaluated against any scheme catalog.
        Returns: (scheme_id or 'unverified_scheme' or 'general_eligibility' or 'document_inquiry' or None, confidence_score)
        """
        if not query:
            return None, 0.0
            
        q_norm = cls.normalize_text(query)
        q_condensed = q_norm.replace(" ", "")

        scheme_index = cls.build_dynamic_scheme_index(schemes)

        # 1. Match against verified scheme index
        best_match = None
        longest_len = 0

        for scheme_id, keywords in scheme_index.items():
            for kw in keywords:
                kw_norm = cls.normalize_text(kw)
                kw_condensed = kw_norm.replace(" ", "")
                if (kw_norm and kw_norm in q_norm) or (kw_condensed and len(kw_condensed) >= 3 and kw_condensed in q_condensed):
                    if len(kw_norm) > longest_len:
                        longest_len = len(kw_norm)
                        best_match = scheme_id

        if best_match:
            return best_match, 0.95

        # 2. Check if the query is a generic follow-up or generic civic question (should retain session context)
        followup_phrases = [
            "what documents", "which documents", "documents do i need", "documents needed",
            "what are the documents", "required documents", "what papers",
            "how to apply", "how do i apply", "where do i apply", "where to apply", "where can i apply",
            "how can i apply", "application process", "where to submit",
            "how long", "how many days", "processing time", "duration", "when will",
            "am i eligible", "who is eligible", "is eligible", "eligibility criteria", "qualify",
            "tell me more", "more details", "provide the details", "give details", "explain",
            "sure", "yes please", "details",
            "which scheme", "all schemes", "what schemes",
            "ದಾಖಲೆಗಳು", "ದಾಖಲೆ", "ಯಾವ ದಾಖಲೆ", "ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ", "ಎಲ್ಲಿ ಅರ್ಜಿ", "ಎಷ್ಟು ದಿನ",
            "ಅರ್ಹತೆ", "ವಿವರ", "ಮಾಹಿತಿ ನೀಡಿ", "ಯಾವ ಯೋಜನೆಗಳು", "ಎಲ್ಲಾ ಯೋಜನೆಗಳು", "ಖಂಡಿತ",
            "दस्तावेज", "कागजात", "आवेदन कैसे करें", "कहाँ आवेदन करें", "कितने दिन", "समय सीमा",
            "पात्रता", "विवरण", "जानकारी", "कौन सी योजना", "सभी योजनाएं", "अवश्य"
        ]
        if any(p in q_norm for p in followup_phrases):
            return None, 0.0

        # 3. Check if query asks about an unknown / unverified named scheme or welfare program
        unverified_scheme_triggers = [
            "scheme", "yojana", "योजना", "ಯೋಜನೆ", "scholarship", "subsidy", "pension", "bima",
            "ಪೆನ್ಷನ್", "ಸಹಾಯಧನ", "ಸ್ಕಾಲರ್‌ಶಿಪ್", "ವಿಮೆ", "पेंशन", "अनुदान", "बीमा", "छात्रवृत्ति"
        ]
        if any(t in q_norm for t in unverified_scheme_triggers):
            return "unverified_scheme", 0.90

        return None, 0.0



    @classmethod
    def classify_sub_intent(cls, query: str) -> str:
        """
        Classifies fine-grained query intent for contextual responses:
        - 'details': Request for comprehensive scheme details/overview
        - 'documents': Questions about required certificates/papers
        - 'application': Questions about where/how to apply, online portals, offices
        - 'eligibility': Questions evaluating criteria, income, age, land
        - 'timeline': Questions about processing duration, days, when card/benefit arrives
        - 'benefits': Questions about monetary grant, foodgrains, insurance amount
        - 'general': General query
        """
        q_norm = cls.normalize_text(query)

        # Timeline indicators
        timeline_kws = [
            "how long", "time", "days", "duration", "when", "processing time", "how many days",
            "ಎಷ್ಟು ದಿನ", "ಎಷ್ಟು ಸಮಯ", "ಯಾವಾಗ", "ದಿನಗಳು", "ಕಾಲಾವಕಾಶ",
            "कितना समय", "कितने दिन", "कब", "समय सीमा", "अवधि", "कितने समय"
        ]
        if any(w in q_norm for w in timeline_kws):
            return "timeline"

        # Document indicators
        doc_kws = [
            "document", "documents", "kagaz", "certificate", "certificates", "passbook", "aadhaar", "proof", "papers",
            "ದಾಖಲೆ", "ದಾಖಲೆಗಳು", "ಪ್ರಮಾಣಪತ್ರ", "ಕಾಗದ", "ಆಧಾರ್", "ಪಾಸ್‌ಬುಕ್", "ಪುರಾವೆ",
            "कागजात", "दस्तावेज", "प्रमाण पत्र", "आधार", "पासबुक", "कागज़", "प्रमाणपत्र"
        ]
        if any(w in q_norm for w in doc_kws):
            return "documents"

        # Application / Where / How / Portal indicators
        apply_kws = [
            "apply", "how to apply", "how do i apply", "how can i apply", "where to apply", "where do i apply",
            "where can i apply", "where", "how", "process", "portal", "website", "online", "submit", "office",
            "ಅರ್ಜಿ", "ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು", "ಹೇಗೆ", "ಎಲ್ಲಿ", "ಪೋರ್ಟಲ್", "ವೆಬ್‌ಸೈಟ್", "ಆನ್‌ಲೈನ್", "ಕಚೇರಿ", "ಸಲ್ಲಿಸಬೇಕು", "ಕೇಂದ್ರ",
            "आवेदन", "आवेदन कैसे करें", "कहाँ आवेदन करें", "कहा आवेदन", "पोर्टल", "वेबसाइट", "ऑनलाइन", "कार्यालय", "केंद्र", "कहाँ", "कैसे"
        ]
        if any(w in q_norm for w in apply_kws):
            return "application"

        # Eligibility indicators
        elig_kws = [
            "eligible", "eligibility", "qualify", "criteria", "am i eligible", "who is eligible", "income limit",
            "ಅರ್ಹತೆ", "ಅರ್ಹನೆ", "ಅರ್ಹರೇ", "ಮಾನದಂಡ", "ನನಗೆ ಸಿಗುತ್ತದೆಯೇ", "ಆದಾಯ ಮಿತಿ",
            "पात्रता", "पात्र", "क्या मैं पात्र हूँ", "नियम", "आय सीमा", "पात्रता शर्तें"
        ]
        if any(w in q_norm for w in elig_kws):
            return "eligibility"

        # Benefit indicators
        benefit_kws = [
            "benefit", "benefits", "money", "grant", "entitlement", "amount", "financial assistance",
            "ಪ್ರಯೋಜನ", "ಪ್ರಯೋಜನಗಳು", "ಹಣ", "ಮೊತ್ತ", "ಸಹಾಯಧನ", "ಲಾಭ",
            "लाभ", "फायदे", "पैसा", "राशि", "अनुदान", "सहायता राशि"
        ]
        if any(w in q_norm for w in benefit_kws):
            return "benefits"

        # Details / Overview / Tell more indicators
        details_kws = [
            "detail", "details", "provide the details", "give details", "tell me more", "more details", "explain", "information",
            "sure", "yes please", "know more", "about", "overview", "what is",
            "ವಿವರ", "ವಿವರಗಳು", "ಮಾಹಿತಿ", "ತಿಳಿಸಿ", "ಹೇಳಿ", "ಹೆಚ್ಚಿನ ವಿವರ", "ಖಂಡಿತ",
            "विवरण", "जानकारी", "विस्तार", "बताएं", "दीजिए", "और बताएं", "अवश्य"
        ]
        if any(w in q_norm for w in details_kws):
            return "details"

        return "general"


language_service = VaniLanguageService()

