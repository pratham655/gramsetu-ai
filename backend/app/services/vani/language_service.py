from typing import List, Dict, Any, Tuple, Optional
from app.schemas.vani import VaniLanguageInfo
import re

SUPPORTED_LANGUAGES: List[VaniLanguageInfo] = [
    VaniLanguageInfo(
        code="kn",
        locale="kn-IN",
        name="Kannada",
        native_name="ಕನ್ನಡ",
        supported_for_stt=True,
        supported_for_tts=True,
        sample_queries=[
            "ನನಗೆ 2.5 ಎಕರೆ ಜಮೀನಿದೆ, ಯಾವ ಯೋಜನೆ ಸಿಗುತ್ತದೆ?",
            "ಪಿಎಂ ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
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
            "How much financial grant does PMAY-G provide?",
            "Am I eligible for Raitha Vidya Nidhi in Karnataka?",
            "How does Ayushman Bharat cashless insurance work?",
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
            "ఆయుష్మాన్ భారత్ ద్వారా ఎంత బీమా లభిస్తుంది?",
        ],
    ),
]

# Canonical scheme keyword associations across languages
SCHEME_KEYWORD_MAP = {
    "pm-kisan-001": [
        "pm-kisan", "pm kisan", "kisan", "kisan samman", "farmer", "agriculture", "landholder",
        "ಕಿಸಾನ್", "ಪಿಎಂ ಕಿಸಾನ್", "ರೈತ", "ಕೃಷಿ", "ಜಮೀನು", "ಭೂಮಿ", "ಖಾತೆ",
        "किसान", "पीएम किसान", "खेती", "जमीन", "खाता", "खसरा",
    ],
    "pmay-g-002": [
        "pmay", "pmay-g", "awas", "housing", "pucca house", "kutcha house", "homeless", "bpl housing",
        "ಆವಾಸ್", "ಪಿಎಂ ಆವಾಸ್", "ಮನೆ ಯೋಜನೆ", "ವಸತಿ", "ಪಕ್ಕಾ ಮನೆ", "ಬಿಪಿಎಲ್ ಮನೆ",
        "आवास", "पीएम आवास", "मकान", "पक्का मकान", "बीपीएल आवास", "झोपड़ी",
    ],
    "pmmvy-003": [
        "pmmvy", "matru vandana", "maternity", "pregnant", "mother", "lactating", "cash incentive",
        "ಮಾತೃ ವಂದನಾ", "ಗರ್ಭಿಣಿ", "ತಾಯಿ", "ಹೆರಿಗೆ ಭತ್ಯೆ",
        "मातृ वंदना", "गर्भवती", "माँ", "प्रसूति सहायता", "शिशु",
    ],
    "pm-jay-004": [
        "pm-jay", "pmjay", "ayushman", "ayushman bharat", "health insurance", "5 lakh", "hospital", "cashless",
        "ಆಯುಷ್ಮಾನ್", "ಪಿಎಂ ಜಯ್", "ಆರೋಗ್ಯ", "5 ಲಕ್ಷ", "ಆಸ್ಪತ್ರೆ", "ಚಿಕಿತ್ಸೆ",
        "आयुष्मान", "आयुष्मान भारत", "स्वास्थ्य बीमा", "5 लाख", "अस्पताल", "इलाज",
    ],
    "raitha-vidya-005": [
        "raitha vidya", "vidya nidhi", "scholarship", "karnataka scholarship", "farmer children", "education",
        "ರೈತ ವಿದ್ಯಾ", "ವಿದ್ಯಾನಿಧಿ", "ವಿದ್ಯಾರ್ಥಿವೇತನ", "ಶಿಕ್ಷಣ", "ಕಾಲೇಜು ಶುಲ್ಕ",
        "विद्या निधि", "छात्रवृत्ति", "किसान छात्रवृत्ति", "पढ़ाई",
    ],
}


class VaniLanguageService:
    """
    Multilingual intent and translation normalization service for regional Indian languages.
    """

    @classmethod
    def get_supported_languages(cls) -> List[VaniLanguageInfo]:
        return SUPPORTED_LANGUAGES

    @classmethod
    def normalize_language_code(cls, lang: str) -> str:
        """
        Normalizes language code (e.g. 'kn-IN' -> 'kn', 'hi-IN' -> 'hi', 'en-US' -> 'en').
        Defaults to 'kn' for Karnataka GramSetu context if unspecified.
        """
        if not lang:
            return "kn"
        clean = lang.strip().lower()
        if clean.startswith("kn"):
            return "kn"
        elif clean.startswith("hi"):
            return "hi"
        elif clean.startswith("te"):
            return "te"
        elif clean.startswith("ta"):
            return "ta"
        elif clean.startswith("mr"):
            return "mr"
        elif clean.startswith("en"):
            return "en"
        return "kn"

    @classmethod
    def get_locale_for_language(cls, lang_code: str) -> str:
        code = cls.normalize_language_code(lang_code)
        match = next((l for l in SUPPORTED_LANGUAGES if l.code == code), None)
        return match.locale if match else "kn-IN"

    @classmethod
    def detect_scheme_intent(cls, query: str) -> Tuple[Optional[str], float]:
        """
        Identifies if user query relates to a specific verified government scheme across English, Kannada, Hindi.
        Returns: (scheme_id or None, confidence_score)
        """
        q_low = query.lower()

        # Direct ID or alias checks
        for scheme_id, keywords in SCHEME_KEYWORD_MAP.items():
            for kw in keywords:
                if kw in q_low:
                    return scheme_id, 0.95

        # Check for general intent keywords
        if any(w in q_low for w in ["scheme", "yojana", "ಯೋಜನೆ", "ಯೋಜನೆಗಳು", "योजना", "योजनाएं", "eligible", "ಅರ್ಹತೆ", "पात्रता"]):
            return "general_eligibility", 0.80

        if any(w in q_low for w in ["document", "kagaz", "ದಾಖಲೆ", "ಪ್ರಮಾಣಪತ್ರ", "कागजात", "दस्तावेज", "aadhaar", "ಆಧಾರ್", "आधार"]):
            return "document_inquiry", 0.85

        return None, 0.50


language_service = VaniLanguageService()
