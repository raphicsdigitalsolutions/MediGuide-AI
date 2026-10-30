"""Validation, safe JSON parsing, and small rendering helpers."""

import hashlib
import json
import re
from typing import Any


EXPECTED_KEYS = {
    "summary",
    "possible_conditions",
    "urgency_level",
    "recommended_next_steps",
    "questions_for_doctor",
    "warning_signs",
}
VALID_URGENCY_LEVELS = {"LOW", "MEDIUM", "HIGH", "EMERGENCY"}
_UNSAFE_MEDICAL_PATTERNS = [
    re.compile(
        r"\b(over[\s-]+the[\s-]+counter|OTC|medications?|medicines?|drugs?|"
        r"remed(?:y|ies)|home[\s-]+remed(?:y|ies)|dosage|doses?|supplements?|"
        r"painkillers?|antibiotics?|antihistamines?|decongestants?|"
        r"acetaminophen|paracetamol|ibuprofen|aspirin)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b\d+(?:\.\d+)?\s*°?\s*(?:F|C)\b", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|μg|g|ml)\b", re.IGNORECASE),
]


class UnsafeMedicalOutputError(ValueError):
    """Raised when generated text contains medication advice or numeric thresholds."""


def contains_unsafe_medical_advice(text: str) -> bool:
    """Detect medication/product advice and specific temperature or dose values."""
    return any(pattern.search(text) for pattern in _UNSAFE_MEDICAL_PATTERNS)


def _all_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _all_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _all_strings(nested)


def validate_age(value: str) -> tuple[int | None, str | None]:
    """Validate the age text input without raising a UI-breaking exception."""
    cleaned = value.strip()
    if not cleaned:
        return None, "Enter an age to continue."
    if not re.fullmatch(r"\d{1,3}", cleaned):
        return None, "Enter age as a whole number from 0 to 120."
    age = int(cleaned)
    if not 0 <= age <= 120:
        return None, "Enter an age from 0 to 120."
    return age, None


def _decode_json_object(raw_text: str) -> dict[str, Any]:
    """Read a JSON object from plain text or accidental Markdown fences."""
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    decoder = json.JSONDecoder()

    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value

    raise ValueError("The model did not return a readable JSON object.")


def parse_assessment(raw_text: str) -> dict[str, Any]:
    """Parse and validate the exact assignment response shape."""
    data = _decode_json_object(raw_text)
    if any(contains_unsafe_medical_advice(item) for item in _all_strings(data)):
        raise UnsafeMedicalOutputError(
            "The model response included medication advice or a specific medical threshold."
        )
    if set(data) != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - set(data))
        extra = sorted(set(data) - EXPECTED_KEYS)
        details = []
        if missing:
            details.append(f"missing keys: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected keys: {', '.join(extra)}")
        raise ValueError("JSON schema mismatch (" + "; ".join(details) + ").")

    if not isinstance(data["summary"], str):
        raise ValueError("The summary must be a string.")

    urgency = str(data["urgency_level"]).strip().upper()
    if urgency not in VALID_URGENCY_LEVELS:
        raise ValueError("Urgency must be LOW, MEDIUM, HIGH, or EMERGENCY.")

    conditions = data["possible_conditions"]
    if not isinstance(conditions, list):
        raise ValueError("possible_conditions must be a list.")
    clean_conditions: list[dict[str, str]] = []
    for item in conditions:
        if not isinstance(item, dict) or set(item) != {"name", "reason"}:
            raise ValueError("Each possible condition must contain name and reason.")
        if not isinstance(item["name"], str) or not isinstance(item["reason"], str):
            raise ValueError("Condition name and reason must be strings.")
        clean_conditions.append({"name": item["name"], "reason": item["reason"]})

    list_fields = [
        "recommended_next_steps",
        "questions_for_doctor",
        "warning_signs",
    ]
    clean_lists: dict[str, list[str]] = {}
    for key in list_fields:
        value = data[key]
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ValueError(f"{key} must be a list of strings.")
        clean_lists[key] = value

    return {
        "summary": data["summary"],
        "possible_conditions": clean_conditions,
        "urgency_level": urgency,
        **clean_lists,
    }


def make_cache_key(patient_data: dict[str, Any], model: str, language: str) -> str:
    """Hash form values so raw inputs are not used as session-cache keys."""
    payload = json.dumps(
        {"patient": patient_data, "model": model, "language": language},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stream_text_chunks(text: str):
    """Yield short chunks for st.write_stream when replaying an in-session result."""
    if not text:
        return
    for word in text.split():
        yield word + " "

