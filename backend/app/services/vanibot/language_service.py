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

# Canonical scheme keyword associations across languages
SCHEME_KEYWORD_MAP = {
    "pm-kisan-001": [
        "pm-kisan", "pm kisan", "kisan", "kisan samman", "farmer", "agriculture", "landholder",
        "ಕಿಸಾನ್", "ಪಿಎಂ ಕಿಸಾನ್", "ರೈತ", "ಕೃಷಿ", "ಜಮೀನು", "ಭೂಮಿ", "ಖಾತೆ", "ಖತೌನಿ",
        "किसान", "पीएम किसान", "खेती", "जमीन", "खाता", "खसरा", "किसान सम्मान निधि",
    ],
    "pmay-g-002": [
        "pmay", "pmay-g", "pmayg", "awas", "housing", "pucca house", "kutcha house", "homeless", "bpl housing", "shelter",
        "ಆವಾಸ್", "ಪಿಎಂ ಆವಾಸ್", "ಮನೆ ಯೋಜನೆ", "ವಸತಿ", "ಪಕ್ಕಾ ಮನೆ", "ಬಿಪಿಎಲ್ ಮನೆ", "ಗುಡಿಸಲು",
        "आवास", "पीएम आवास", "मकान", "पक्का मकान", "बीपीएल आवास", "झोपड़ी", "घर",
    ],
    "pmmvy-003": [
        "pmmvy", "matru vandana", "maternity", "pregnant", "mother", "lactating", "cash incentive", "childbirth",
        "ಮಾತೃ ವಂದನಾ", "ಗರ್ಭಿಣಿ", "ತಾಯಿ", "ಹೆರಿಗೆ ಭತ್ಯೆ", "ಶಿಶು",
        "मातृ वंदना", "गर्भवती", "माँ", "प्रसूति सहायता", "शिशु", "मातृत्व",
    ],
    "pm-jay-004": [
        "pm-jay", "pmjay", "ayushman", "ayushman bharat", "health insurance", "5 lakh", "hospital", "cashless", "treatment",
        "ಆಯುಷ್ಮಾನ್", "ಪಿಎಂ ಜಯ್", "ಆರೋಗ್ಯ", "5 ಲಕ್ಷ", "ಆಸ್ಪತ್ರೆ", "ಚಿಕಿತ್ಸೆ", "ವಿಮೆ",
        "आयुष्मान", "आयुष्मान भारत", "स्वास्थ्य बीमा", "5 लाख", "अस्पताल", "इलाज", "चिकित्सा",
    ],
    "raitha-vidya-005": [
        "raitha vidya", "vidya nidhi", "scholarship", "karnataka scholarship", "farmer children", "education", "student grant",
        "ರೈತ ವಿದ್ಯಾ", "ವಿದ್ಯಾನಿಧಿ", "ವಿದ್ಯಾರ್ಥಿವೇತನ", "ಶಿಕ್ಷಣ", "ಕಾಲೇಜು ಶುಲ್ಕ", "ರೈತರ ಮಕ್ಕಳು",
        "विद्या निधि", "छात्रवृत्ति", "किसान छात्रवृत्ति", "पढ़ाई", "छात्र अनुदान",
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
        if not query:
            return None, 0.0
            
        q_low = query.lower()

        # Direct ID or keyword checks
        for scheme_id, keywords in SCHEME_KEYWORD_MAP.items():
            for kw in keywords:
                if kw in q_low:
                    return scheme_id, 0.95

        # Check for general intent keywords
        if any(w in q_low for w in ["scheme", "yojana", "ಯೋಜನೆ", "ಯೋಜನೆಗಳು", "योजना", "योजनाएं", "eligible", "ಅರ್ಹತೆ", "पात्रता"]):
            return "general_eligibility", 0.80

        if any(w in q_low for w in ["document", "documents", "kagaz", "ದಾಖಲೆ", "ಪ್ರಮಾಣಪತ್ರ", "कागजात", "दस्तावेज", "aadhaar", "ಆಧಾರ್", "आधार", "passbook"]):
            return "document_inquiry", 0.85

        return None, 0.50


language_service = VaniLanguageService()
