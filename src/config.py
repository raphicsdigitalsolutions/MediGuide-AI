"""Project settings and the small set of form choices used by the UI."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)

APP_NAME = "MediGuide AI"
APP_SUBTITLE = "Educational symptom information and patient guidance prototype"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_CACHE_PATH = PROJECT_ROOT / "data" / "langchain_cache.db"


def get_server_api_key() -> str:
    """Read a deployment secret first, then the local dotenv environment."""
    secret_key = ""
    try:
        import streamlit as st

        secret_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        # A local app may not have a secrets.toml file; dotenv remains supported.
        secret_key = ""
    return secret_key or os.getenv("OPENAI_API_KEY", "").strip()

SAFETY_DISCLAIMER = (
    "Educational prototype only. MediGuide AI is not a doctor and cannot diagnose, "
    "recommend treatment, or replace a licensed healthcare professional. If symptoms "
    "are severe, worsening, or feel urgent, contact local emergency services or a "
    "qualified healthcare professional now. Do not wait for this app in an emergency."
)

SYMPTOM_OPTIONS = [
    "Fever",
    "Cough",
    "Runny nose",
    "Sore throat",
    "Headache",
    "Nausea",
    "Vomiting",
    "Diarrhea",
    "Abdominal pain",
    "Chest pain",
    "Shortness of breath",
    "Fatigue",
    "Dizziness",
    "Rash",
    "Other",
]

DURATION_OPTIONS = [
    "Less than 24 hours",
    "1–3 days",
    "4–7 days",
    "1–2 weeks",
    "More than 2 weeks",
    "Unsure",
]

GENDER_OPTIONS = [
    "Prefer not to say",
    "Female",
    "Male",
    "Non-binary",
    "Self-describe",
]

LANGUAGE_OPTIONS = ["English", "Urdu"]
MODEL_OPTIONS = ["gpt-4o-mini", "gpt-4.1-mini"]
CACHE_OPTIONS = ["Off", "In-memory", "SQLite"]

