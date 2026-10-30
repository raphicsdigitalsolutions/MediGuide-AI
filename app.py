"""Streamlit interface for the educational MediGuide AI assignment prototype."""

import streamlit as st

from src.cache_manager import clear_active_cache, configure_llm_cache, llm_cache_context
from src.chains import create_chat_model, build_assessment_chain, stream_narrative, demonstrate_message_roles
from src.config import (
    APP_NAME, APP_SUBTITLE, CACHE_OPTIONS, DEFAULT_CACHE_PATH, DEFAULT_MODEL,
    DURATION_OPTIONS, GENDER_OPTIONS, get_server_api_key, LANGUAGE_OPTIONS,
    MODEL_OPTIONS, SAFETY_DISCLAIMER, SYMPTOM_OPTIONS,
)
from src.safety import detect_emergency, emergency_assessment
from src.utils import (
    UnsafeMedicalOutputError, make_cache_key, parse_assessment,
    stream_text_chunks, validate_age,
)

st.set_page_config(page_title=APP_NAME, page_icon="🩺", layout="wide")

st.markdown(
    """
    <style>
    .stApp {background: radial-gradient(ellipse at 85% 0%, #153c40 0%, transparent 38%),
             linear-gradient(145deg,#08171d,#0c252b 62%,#091a20); color:#e8f3f0;}
    [data-testid="stSidebar"] {background:#0b2026;}
    .block-container {max-width:1180px;padding-top:2rem;padding-bottom:3rem;}
    .hero {padding:1.5rem 0 1rem;}
    .eyebrow {color:#72dfc8;text-transform:uppercase;letter-spacing:.16em;font-size:.75rem;font-weight:700;}
    .hero h1 {font-size:3rem;line-height:1.05;color:#f1fbf8;margin:.5rem 0;}
    .hero p {font-size:1.05rem;color:#b8cfca;max-width:760px;}
    .notice {padding:1rem 1.1rem;border:1px solid #9b7842;border-radius:14px;background:#332b1d;color:#f5e5c5;margin:.7rem 0 1.2rem;}
    div[data-testid="stMetric"] {background:#102b31;padding:1rem;border:1px solid #23464a;border-radius:14px;}
    </style>
    """,
    unsafe_allow_html=True,
)

def show_disclaimer():
    st.warning(f"**Medical safety notice:** {SAFETY_DISCLAIMER}")

def render_results(result: dict, narrative: str | None = None):
    urgency = result["urgency_level"]
    if urgency == "EMERGENCY":
        st.error("EMERGENCY — seek local emergency help immediately. Do not wait for this app.")
    elif urgency == "HIGH":
        st.warning("HIGH urgency estimate — contact a qualified healthcare professional promptly.")
    elif urgency == "MEDIUM":
        st.info("MEDIUM urgency estimate — consider speaking with a qualified healthcare professional.")
    else:
        st.success("LOW urgency estimate — this is not a medical clearance or diagnosis.")

    a, b, c = st.columns(3)
    a.metric("Urgency level", urgency)
    b.metric("Possible conditions", len(result["possible_conditions"]))
    c.metric("Next steps", len(result["recommended_next_steps"]))

    tabs = st.tabs(["Overview", "Possible conditions", "Next steps", "Doctor questions", "Warning signs"])
    with tabs[0]:
        st.subheader("Symptom summary")
        st.write(result["summary"])
        if narrative:
            st.subheader("Live guidance narrative")
            st.write(narrative)
    with tabs[1]:
        st.caption("Educational possibilities only. These are not diagnoses.")
        if result["possible_conditions"]:
            for item in result["possible_conditions"]:
                with st.expander(item["name"]):
                    st.write(item["reason"])
        else:
            st.write("No possible conditions were returned.")
    with tabs[2]:
        for item in result["recommended_next_steps"]:
            st.markdown(f"- {item}")
    with tabs[3]:
        for item in result["questions_for_doctor"]:
            st.markdown(f"- {item}")
    with tabs[4]:
        for item in result["warning_signs"]:
            st.markdown(f"- {item}")
    show_disclaimer()


def run_assessment(patient: dict, model_name: str, language: str, cache_mode: str, api_key: str):
    cache_key = make_cache_key(patient, model_name, language)
    session_cache = st.session_state.setdefault("assessment_cache", {})
    if cache_mode != "Off" and cache_key in session_cache:
        st.info("Session cache hit — replaying the previously generated result.")
        cached = session_cache[cache_key]
        st.write_stream(stream_text_chunks(cached["narrative"]))
        render_results(cached["assessment"], cached["narrative"])
        return

    llm = create_chat_model(model_name, api_key)
    patient_details = (
        f"Age: {patient['age']}\nGender: {patient['gender']}\n"
        f"Symptoms: {', '.join(patient['symptoms'])}\nDuration: {patient['duration']}\n"
        f"Self-reported severity: {patient['severity']}/10\n"
        f"Existing conditions: {patient['conditions'] or 'Not provided'}\n"
        f"Current medications: {patient['medications'] or 'Not provided'}\n"
        f"Additional notes: {patient['notes'] or 'Not provided'}\n"
        f"Requested language: {language}"
    )

    with llm_cache_context(cache_mode, DEFAULT_CACHE_PATH):
        chain = build_assessment_chain(llm)
        response = chain.invoke({"patient_details": patient_details})
        raw_response = response.get("assessment_json", "")
        try:
            assessment = parse_assessment(raw_response)
        except (ValueError, UnsafeMedicalOutputError) as exc:
            st.error(f"The AI response could not be safely validated: {exc}")
            with st.expander("Raw model response for debugging"):
                st.code(str(raw_response), language="json")
            return

        st.subheader("Live response")
        narrative = st.write_stream(stream_narrative(llm, raw_response, language))
    if cache_mode != "Off":
        session_cache[cache_key] = {"assessment": assessment, "narrative": narrative or ""}
    render_results(assessment, narrative or "")


st.sidebar.title("🩺 MediGuide AI")
st.sidebar.caption(APP_SUBTITLE)
st.sidebar.markdown("---")
st.sidebar.warning(SAFETY_DISCLAIMER)
st.sidebar.subheader("Model configuration")

server_key = get_server_api_key()
visitor_key = ""
if server_key:
    st.sidebar.success("App-configured API connection available.")
    api_key = server_key
    cache_mode = st.sidebar.selectbox("Model cache", CACHE_OPTIONS, index=1)
else:
    st.sidebar.info("Connect an API key to generate non-emergency guidance.")
    visitor_key = st.sidebar.text_input("OpenAI API key (session only)", type="password")
    api_key = visitor_key.strip()
    cache_mode = "Off" if api_key else "Off"
    if api_key:
        st.sidebar.caption("Caching is disabled for visitor-provided keys.")
model_default = DEFAULT_MODEL if DEFAULT_MODEL in MODEL_OPTIONS else MODEL_OPTIONS[0]
model_name = st.sidebar.selectbox("OpenAI model", MODEL_OPTIONS, index=MODEL_OPTIONS.index(model_default))
language = st.sidebar.selectbox("Answer language", LANGUAGE_OPTIONS, index=0)
st.sidebar.caption("SQLite cache stores prompts and responses locally without encryption. Use fictional demo data only.")
if st.sidebar.button("Clear selected model cache", disabled=(cache_mode == "Off")):
    clear_active_cache()
    st.session_state["assessment_cache"] = {}
    st.sidebar.success("Selected cache cleared.")

st.markdown(
    f'<div class="hero"><div class="eyebrow">LangChain · Streamlit · OpenAI</div>'
    f'<h1>{APP_NAME}</h1><p>{APP_SUBTITLE}. Enter fictional symptom details to view cautious, structured educational information.</p></div>',
    unsafe_allow_html=True,
)
show_disclaimer()

with st.form("patient_information"):
    st.subheader("Patient information")
    col1, col2, col3 = st.columns(3)
    with col1:
        age_text = st.text_input("Age", placeholder="Whole years")
    with col2:
        gender = st.selectbox("Gender", GENDER_OPTIONS)
    with col3:
        duration = st.selectbox("Symptom duration", DURATION_OPTIONS)
    symptoms = st.multiselect("Symptoms", SYMPTOM_OPTIONS, help="Select all that apply.")
    free_symptoms = st.text_area("Additional symptom details", height=75, placeholder="Optional; do not include names or identifying details.")
    severity = st.slider("Overall self-reported severity", 1, 10, 3)
    col4, col5 = st.columns(2)
    with col4:
        conditions = st.text_area("Existing medical conditions", height=95)
        medications = st.text_area("Current medications", height=95)
    with col5:
        notes = st.text_area("Additional notes", height=203)
    st.caption("Use fictional details only. Do not enter names, addresses, phone numbers, or real patient identifiers.")
    submitted = st.form_submit_button("Generate educational guidance", type="primary", use_container_width=True)

if submitted:
    age, age_error = validate_age(age_text)
    all_symptoms = [s for s in symptoms if s != "Other"]
    if free_symptoms.strip():
        all_symptoms.append(free_symptoms.strip())
    if not all_symptoms:
        st.warning("Enter or select at least one symptom. No API call was made.")
    elif age_error:
        st.warning(age_error)
    else:
        patient = {
            "age": age, "gender": gender, "symptoms": all_symptoms,
            "duration": duration, "severity": severity,
            "conditions": conditions.strip(), "medications": medications.strip(),
            "notes": notes.strip(),
        }
        if detect_emergency(all_symptoms, notes):
            urgent = emergency_assessment(language)
            st.session_state["last_result"] = {"assessment": urgent, "narrative": ""}
            render_results(urgent)
        elif not api_key:
            st.error("Add an OpenAI API key in the sidebar, or configure OPENAI_API_KEY in Streamlit Secrets.")
        else:
            try:
                run_assessment(patient, model_name, language, cache_mode, api_key)
            except Exception as exc:
                st.error("The guidance request could not be completed. Check the API key, model access, and internet connection, then try again.")
                with st.expander("Technical details"):
                    st.exception(exc)

with st.expander("How the LangChain message roles fit together"):
    st.caption("SystemMessage provides rules, HumanMessage carries user input, and AIMessage represents an assistant response in conversation history. The following example is fictional.")
    for message in demonstrate_message_roles():
        st.markdown(f"**{message.type.title()}Message**")
        st.code(str(message.content), language="text")

st.caption("MediGuide AI is an educational software prototype, not a medical device. Do not use it for real diagnosis or treatment.")
