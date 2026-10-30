"""Small, best-effort emergency phrase check for the educational prototype."""

import re
from collections.abc import Iterable


# This narrow keyword check cannot recognize every emergency or rule one out.
_EMERGENCY_PATTERNS = [
    re.compile(
        r"\b(chest pain|chest pressure|chest tightness)\b.{0,80}\b"
        r"(shortness of breath|difficulty breathing|trouble breathing|can't breathe|"
        r"cannot breathe|gasping|breathless)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(shortness of breath|difficulty breathing|trouble breathing|can't breathe|"
        r"cannot breathe|gasping|breathless)\b.{0,80}\b"
        r"(chest pain|chest pressure|chest tightness)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(severe|sudden|crushing|persistent)\s+(chest pain|chest pressure|"
        r"chest tightness)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(severe|sudden|worsening)\s+(shortness of breath|difficulty breathing|"
        r"trouble breathing|breathlessness)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(unconscious|unresponsive|not responding|passed out|severe bleeding|"
        r"bleeding heavily|choking|anaphylaxis|severe allergic reaction)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(saans lenay mein shadeed dushwari|saans nahin aa rahi|seene mein shadeed dard|"
        r"behosh|shadeed khoon behna)",
        re.IGNORECASE,
    ),
]


def detect_emergency(symptoms: Iterable[str], notes: str = "") -> bool:
    """Return True for a few high-risk phrases; this is not medical triage."""
    text = " ".join([*symptoms, notes]).strip()
    return any(pattern.search(text) for pattern in _EMERGENCY_PATTERNS)


def emergency_assessment(language: str) -> dict[str, object]:
    """Return a conservative, non-diagnostic fallback without calling an LLM."""
    if language == "Urdu":
        return {
            "summary": (
                "آپ کی دی گئی معلومات میں ایسی علامات شامل ہیں جن کے لیے فوری طبی "
                "معائنہ ضروری ہو سکتا ہے۔ یہ ایپ وجہ کی تشخیص نہیں کر سکتی۔"
            ),
            "possible_conditions": [],
            "urgency_level": "EMERGENCY",
            "recommended_next_steps": [
                "ابھی مقامی ایمرجنسی سروس سے رابطہ کریں یا قریبی ایمرجنسی ڈیپارٹمنٹ جائیں۔ اس ایپ کا انتظار نہ کریں۔"
            ],
            "questions_for_doctor": [],
            "warning_signs": [
                "اگر یہ علامات ابھی موجود ہیں یا بڑھ رہی ہیں تو فوراً ہنگامی مدد حاصل کریں۔"
            ],
        }

    return {
        "summary": (
            "Your description includes symptoms that can need immediate assessment. "
            "This app cannot determine the cause."
        ),
        "possible_conditions": [],
        "urgency_level": "EMERGENCY",
        "recommended_next_steps": [
            "Contact local emergency services now or go to the nearest emergency department. Do not wait for this app."
        ],
        "questions_for_doctor": [],
        "warning_signs": [
            "If these symptoms are happening now or getting worse, seek emergency help immediately."
        ],
    }

