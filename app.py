"""Streamlit UI for the educational MediGuide AI assignment prototype."""

import json
import streamlit as st

from src.cache_manager import clear_active_cache, configure_llm_cache, llm_cache_context
from src.chains import (
    build_assessment_chain,
    create_chat_model,
    demonstrate_message_roles,
    stream_narrative,
)
from src.config import (
    APP_NAME,
    APP_SUBTITLE,
    CACHE_OPTIONS,
    DEFAULT_CACHE_PATH,
    DEFAULT_MODEL,
    DURATION_OPTIONS,
    GENDER_OPTIONS,
    get_server_api_key,
    LANGUAGE_OPTIONS,
    MODEL_OPTIONS,
    SAFETY_DISCLAIMER,
    SYMPTOM_OPTIONS,
)
from src.prompts import ASSESSMENT_PROMPT_TEMPLATE
from src.safety import detect_emergency, emergency_assessment
from src.utils import (
    UnsafeMedicalOutputError,
    contains_unsafe_medical_advice,
    make_cache_key,
    parse_assessment,
    stream_text_chunks,
    validate_age,
)


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.session_state.setdefault("day_mode", False)
day_mode = bool(st.session_state.get("day_mode", False))

st.markdown(
    """
    <style>
      :root { color-scheme: dark; }
      .stApp, [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(ellipse at 78% 3%, rgba(38, 188, 160, .13), transparent 34%),
          radial-gradient(ellipse at 4% 34%, rgba(42, 105, 128, .12), transparent 30%),
          linear-gradient(145deg, #07151a 0%, #0b2026 52%, #08171d 100%);
        color: #e9f3f1;
        font-family: "Segoe UI Variable", "Aptos", ui-sans-serif, system-ui, sans-serif;
      }
      /* Keep Streamlit's Material Symbols font on buttons; overriding button fonts
         turns icon ligatures such as arrow_right into visible text. */
      html, body, input, textarea { font-family: "Segoe UI Variable", "Aptos", ui-sans-serif, system-ui, sans-serif; }
      [data-testid="stHeader"] { background: rgba(7, 21, 26, .78); }
      [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, #0d2228 0%, #091a1f 100%);
        border-right: 1px solid rgba(191, 244, 234, .08);
      }
      .block-container { max-width: 1380px; padding: 2.6rem 2.3rem 5rem; }
      h1, h2, h3 { color: #f3f8f7; letter-spacing: -.035em; }
      [data-testid="stSidebar"] h1 { font-size: 1.35rem !important; line-height: 1.2 !important; letter-spacing: -.02em; white-space: nowrap; }
      [data-testid="stSidebar"] h2 { font-size: 1rem !important; letter-spacing: -.01em; }
      p, label, [data-testid="stMarkdownContainer"] { color: #b8cbc9; }
      .hero-copy-block { padding: 1.5rem 0 1.9rem; }
      .hero-eyebrow, .section-eyebrow {
        display: inline-flex; align-items: center; gap: .55rem;
        color: #79deca; font-size: .72rem; font-weight: 750;
        letter-spacing: .18em; text-transform: uppercase;
      }
      .hero-eyebrow-dot { width: 7px; height: 7px; border-radius: 50%; background: #7de6d0; box-shadow: 0 0 18px rgba(125,230,208,.8); }
      .hero-copy-block h1 { margin: 1.1rem 0 1rem; max-width: 760px; font-size: clamp(2.3rem, 4.1vw, 3.9rem) !important; line-height: 1.02 !important; }
      .hero-copy-block h1 span { color: #78dfca; }
      .hero-copy-block p { color: #a8bfbd; font-size: 1.05rem; line-height: 1.7; max-width: 700px; }
      .hero-meta { display: flex; flex-wrap: wrap; gap: .6rem; margin-top: 1.3rem; }
      .hero-meta span { border: 1px solid rgba(189,238,229,.12); border-radius: 999px; padding: .4rem .75rem; color: #c1d5d2; font-size: .74rem; background: rgba(255,255,255,.035); }
      .hero-visual-shell { padding: 1px; border-radius: 30px; background: linear-gradient(140deg, rgba(145,242,220,.42), rgba(255,255,255,.06) 48%, rgba(55,148,143,.3)); box-shadow: 0 24px 80px rgba(0,0,0,.25); transform-style: preserve-3d; transition: transform 520ms cubic-bezier(.32,.72,0,1), box-shadow 520ms cubic-bezier(.32,.72,0,1); }
      .hero-visual-shell:hover { transform: translateY(-3px) rotateX(.5deg); box-shadow: 0 30px 86px rgba(0,0,0,.32); }
      .hero-visual { position: relative; display: grid; place-items: center; min-height: 325px; overflow: hidden; border-radius: 29px; background: radial-gradient(ellipse at 50% 48%, rgba(30,131,123,.23), transparent 50%), linear-gradient(145deg, #102b31, #0a1b21 78%); box-shadow: inset 0 1px rgba(238,255,251,.12); }
      .hero-visual::before { content: ""; position: absolute; inset: 0; pointer-events: none; background: repeating-linear-gradient(0deg, transparent 0 30px, rgba(197,248,239,.025) 31px), repeating-linear-gradient(90deg, transparent 0 30px, rgba(197,248,239,.025) 31px); mask-image: radial-gradient(ellipse at center, #000 5%, transparent 76%); }
      .hero-visual-label { position: absolute; top: 1.2rem; left: 1.3rem; z-index: 2; color: #9ebbb7; font-size: .61rem; letter-spacing: .13em; }
      .hero-visual-status { position: absolute; right: 1.2rem; top: 1.1rem; z-index: 2; display: flex; align-items: center; gap: .45rem; color: #99c5bc; font-size: .6rem; }
      .hero-visual-status i { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #79e3c8; box-shadow: 0 0 12px rgba(121,227,200,.9); }
      .orb-stage { position: relative; width: 270px; height: 235px; perspective: 900px; }
      .orb-halo { position: absolute; inset: 12%; border-radius: 50%; background: radial-gradient(circle, rgba(78,227,196,.18), transparent 68%); }
      .orb-core { position: absolute; z-index: 1; left: 59px; top: 32px; width: 152px; height: 152px; border-radius: 50%; background: radial-gradient(circle at 28% 22%, #e4fff7 0%, #a5f7e3 5%, #48cbb1 20%, #197e7d 48%, #0b424e 75%, #07232d 100%); box-shadow: inset -20px -25px 42px rgba(1,16,22,.74), inset 8px 8px 24px rgba(231,255,247,.34), 0 0 38px rgba(71,215,187,.28), 0 20px 44px rgba(0,0,0,.3); transform: rotateX(12deg) rotateY(-17deg); animation: orb-float 7s cubic-bezier(.32,.72,0,1) infinite alternate; }
      .orb-core::after { content: ""; position: absolute; inset: 30%; border-radius: 50%; border: 1px solid rgba(226,255,248,.38); box-shadow: 0 0 22px rgba(190,255,241,.22); }
      .orb-ring { position: absolute; z-index: 2; left: 14px; top: 74px; width: 242px; height: 86px; border: 1px solid rgba(141,244,222,.55); border-radius: 50%; transform: rotateX(65deg) rotateZ(-19deg); box-shadow: 0 0 20px rgba(81,210,186,.09); animation: ring-drift 18s cubic-bezier(.45,.05,.35,.95) infinite; }
      .orb-ring::after { content: ""; position: absolute; top: 50%; right: 9%; width: 8px; height: 8px; border-radius: 50%; background: #d9fff3; box-shadow: 0 0 14px #8ef3d9; }
      .orb-ring-secondary { left: 35px; top: 65px; width: 200px; height: 120px; border-color: rgba(143,199,213,.34); transform: rotateX(68deg) rotateZ(57deg); animation-duration: 24s; animation-direction: reverse; }
      .hero-visual-foot { position: absolute; bottom: 1.25rem; left: 1.35rem; right: 1.35rem; display: flex; justify-content: space-between; align-items: end; z-index: 2; }
      .hero-visual-foot strong { display: block; color: #e8f7f3; font-size: .86rem; font-weight: 650; }
      .hero-visual-foot small { color: #8da9a6; font-size: .67rem; }
      .hero-visual-foot .orbit-mark { color: #77dfc9; font-size: 1.1rem; }
      [data-testid="stHorizontalBlock"]:has(.hero-copy-block) { flex-wrap: wrap !important; align-items: center; }
      [data-testid="stHorizontalBlock"]:has(.hero-copy-block) > [data-testid="column"]:first-child { flex: 1.25 1 360px !important; min-width: 0; }
      [data-testid="stHorizontalBlock"]:has(.hero-copy-block) > [data-testid="column"]:last-child { flex: .85 1 300px !important; min-width: 0; }
      .safety-banner { display: flex; gap: .8rem; align-items: flex-start; padding: 1rem 1.15rem; margin: .35rem 0 1rem; border: 1px solid rgba(245,196,105,.3); border-radius: 18px; background: linear-gradient(120deg, rgba(122,91,35,.25), rgba(16,39,45,.88) 68%, rgba(255,255,255,.025)); box-shadow: inset 0 1px rgba(255,255,255,.055), 0 12px 34px rgba(0,0,0,.12); color: #f3e3bf; }
      .safety-banner-mark { flex: 0 0 26px; width: 26px; height: 26px; display: grid; place-items: center; border-radius: 9px; color: #17252b; background: linear-gradient(145deg, #ffe2a0, #e9b957); box-shadow: 0 4px 16px rgba(231,183,83,.22); font-size: .8rem; font-weight: 900; }
      .safety-banner strong { display: block; margin-bottom: .16rem; color: #ffe1a0; font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; }
      .safety-banner p { margin: 0; color: #e8dcc0; font-size: .82rem; line-height: 1.55; }
      [data-testid="stSidebar"] .safety-banner { gap: .55rem; padding: .75rem; margin: .5rem 0 1.2rem; border-radius: 15px; }
      [data-testid="stSidebar"] .safety-banner-mark { flex-basis: 22px; width: 22px; height: 22px; }
      [data-testid="stSidebar"] .safety-banner p { font-size: .7rem; line-height: 1.5; }
      [data-testid="stSidebar"] .safety-banner strong { font-size: .63rem; }
      [data-testid="stDialog"] > div { border: 1px solid rgba(150,235,217,.16); border-radius: 28px; background: linear-gradient(145deg, #102a30, #0a1c21 82%); box-shadow: 0 32px 100px rgba(0,0,0,.48), inset 0 1px rgba(255,255,255,.07); }
      [data-testid="stDialog"] h2 { font-size: 1.35rem !important; }
      .key-connect-visual { display: flex; align-items: center; gap: 1rem; padding: .9rem 1rem; margin: .2rem 0 1rem; border: 1px solid rgba(168,238,224,.12); border-radius: 21px; background: radial-gradient(ellipse at 22% 50%, rgba(48,184,161,.16), transparent 56%), rgba(255,255,255,.025); }
      .key-orb-scene { position: relative; flex: 0 0 78px; width: 78px; height: 78px; perspective: 500px; }
      .key-orb { position: absolute; inset: 11px; border-radius: 50%; background: radial-gradient(circle at 28% 22%, #e7fff7, #8debd4 13%, #32b89f 38%, #0d5260 78%, #082b38); box-shadow: inset -9px -11px 19px rgba(0,15,22,.68), inset 4px 4px 12px rgba(230,255,248,.3), 0 0 27px rgba(74,214,184,.27); transform: rotateX(14deg) rotateY(-18deg); }
      .key-orbit { position: absolute; inset: 6px -4px; border: 1px solid rgba(146,244,221,.52); border-radius: 50%; transform: rotateX(65deg) rotateZ(-22deg); animation: ring-drift 13s cubic-bezier(.45,.05,.35,.95) infinite; }
      .key-connect-copy strong { display: block; color: #e9f7f3; margin-bottom: .25rem; }
      .key-connect-copy p { margin: 0; color: #a9c2be; font-size: .82rem; line-height: 1.5; }
      .key-security-note { padding: .8rem .9rem; border-radius: 14px; color: #ddcfad; background: rgba(180,137,62,.1); border: 1px solid rgba(230,188,103,.15); font-size: .75rem; line-height: 1.5; }
      @keyframes orb-float { from { transform: translateY(3px) rotateX(12deg) rotateY(-17deg); } to { transform: translateY(-7px) rotateX(16deg) rotateY(-12deg); } }
      @keyframes ring-drift { from { rotate: 0deg; } to { rotate: 360deg; } }
      .key-orb { animation: orb-float 6s cubic-bezier(.32,.72,0,1) infinite alternate; }
      @media (prefers-reduced-motion: reduce) { .orb-core, .orb-ring, .key-orb, .key-orbit { animation: none; } }
      @media (max-width: 767px) { .block-container { padding: 1.6rem 1rem 3rem; } .hero-visual { min-height: 255px; } .orb-stage { transform: scale(.84); } }
      div[data-testid="stForm"] { border: 1px solid rgba(202,244,237,.1); border-radius: 27px; padding: 1.55rem !important; background: linear-gradient(155deg, rgba(20,45,51,.96), rgba(12,31,37,.98)); box-shadow: inset 0 1px rgba(245,255,252,.08), 0 25px 70px rgba(0,0,0,.2); }
      div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, div[data-baseweb="textarea"] { background: rgba(5,19,23,.58) !important; border-color: rgba(190,235,228,.14) !important; border-radius: 13px !important; }
      div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea { color: #e7f3f0 !important; }
      div[data-testid="stFormSubmitButton"] button { border: 1px solid rgba(174,255,237,.35); border-radius: 999px; background: linear-gradient(135deg, #7de6ce, #38b8a4); color: #06211f !important; -webkit-text-fill-color: #06211f !important; opacity: 1 !important; font-weight: 750; box-shadow: inset 0 1px rgba(255,255,255,.48), 0 10px 30px rgba(44,182,157,.2); transition: transform 520ms cubic-bezier(.32,.72,0,1), box-shadow 520ms cubic-bezier(.32,.72,0,1); }
      div[data-testid="stFormSubmitButton"] button:disabled { color: #174c45 !important; -webkit-text-fill-color: #174c45 !important; opacity: 1 !important; filter: saturate(.78); }
      div[data-testid="stFormSubmitButton"] button p { color: inherit !important; }
      div[data-testid="stFormSubmitButton"] button:hover { transform: translateY(-2px); box-shadow: inset 0 1px rgba(255,255,255,.56), 0 15px 38px rgba(44,182,157,.32); }
      .stButton button { border-radius: 999px; border-color: rgba(194,237,229,.16); background: rgba(255,255,255,.035); color: #c8dbd8; transition: transform 520ms cubic-bezier(.32,.72,0,1), background 520ms cubic-bezier(.32,.72,0,1); }
      .stButton button:hover { transform: translateY(-1px); background: rgba(255,255,255,.08); border-color: rgba(194,237,229,.3); color: #f3fbf9; }
      div[data-testid="stMetric"] { padding: .9rem 1rem; border-radius: 18px; background: linear-gradient(145deg, rgba(255,255,255,.055), rgba(255,255,255,.02)); box-shadow: inset 0 1px rgba(255,255,255,.06); }
      div[data-testid="stMetricValue"] { color: #e7f4f1; }
      div[data-testid="stAlert"] { border-radius: 18px; }
      div[data-testid="stTabs"] button[aria-selected="true"] { color: #82e5d0; }
      .urgency-chip { display: inline-block; border-radius: 999px; padding: .3rem .76rem; font-size: .72rem; font-weight: 800; letter-spacing: .1em; }
      .urgency-low { color: #a5f4d4; background: rgba(34,155,112,.2); border: 1px solid rgba(121,237,187,.22); }
      .urgency-medium { color: #ffe6a2; background: rgba(190,139,38,.18); border: 1px solid rgba(255,212,117,.22); }
      .urgency-high { color: #ffc196; background: rgba(202,105,42,.18); border: 1px solid rgba(255,174,116,.22); }
      .urgency-emergency { color: #ffb2b5; background: rgba(186,55,65,.22); border: 1px solid rgba(255,130,139,.26); }
    </style>
    """,
    unsafe_allow_html=True,
)

if day_mode:
    st.markdown(
        """
        <style>
          :root {
            color-scheme: light;
            --primary-color: #168f81;
            --background-color: #f2f8f9;
            --secondary-background-color: #ffffff;
            --text-color: #173d46;
          }
          html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: #f2f8f9 !important; color: #163b43 !important; }
          [data-testid="stHeader"] { background: rgba(244,251,251,.86) !important; }
          [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { background: #eaf2f3 !important; border-right: 1px solid rgba(35,91,99,.12) !important; min-height: 100vh; }
          [data-testid="stSidebarContent"], [data-testid="stSidebarUserContent"] { background: transparent !important; }
          h1, h2, h3 { color: #173d46 !important; }
          p, label, [data-testid="stMarkdownContainer"] { color: #506a70 !important; }
          [data-testid="stWidgetLabel"] p { color: #355b63 !important; font-weight: 600 !important; }
          .hero-copy-block h1 { color: #173d46 !important; }
          .hero-copy-block h1 span, .hero-eyebrow, .section-eyebrow { color: #128c80 !important; }
          .hero-copy-block p { color: #516b72 !important; }
          .hero-meta span { color: #35575e !important; background: rgba(255,255,255,.72) !important; border-color: rgba(36,105,111,.16) !important; }
          .hero-visual-shell { background: linear-gradient(140deg, rgba(24,150,136,.5), rgba(255,255,255,.9) 48%, rgba(36,125,144,.38)) !important; }
          .safety-banner { background: linear-gradient(120deg, #fff4d7, #fffaf0 72%) !important; border-color: rgba(202,148,48,.34) !important; color: #59491f !important; }
          .safety-banner strong { color: #785514 !important; }
          .safety-banner p { color: #5d553c !important; }
          div[data-testid="stForm"] { background: linear-gradient(155deg, rgba(255,255,255,.96), rgba(242,250,250,.98)) !important; border-color: rgba(41,105,111,.15) !important; box-shadow: inset 0 1px #fff, 0 24px 65px rgba(38,91,98,.12) !important; }
          [data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"], [data-testid="stNumberInputRootElement"] { background: #fff !important; border: 1px solid #bfd0d4 !important; border-radius: 10px !important; box-shadow: none !important; }
          [data-testid="stTextInputField"], [data-testid="stTextAreaRootElement"] textarea, [data-testid="stNumberInputField"] { background: #fff !important; border: 0 !important; color: #173d46 !important; -webkit-text-fill-color: #173d46 !important; box-shadow: none !important; }
          [data-testid="stSelectbox"] [role="group"], [data-testid="stMultiSelect"] [role="group"] { background: #fff !important; border: 1px solid #bfd0d4 !important; border-radius: 10px !important; box-shadow: none !important; }
          [data-testid="stSelectbox"] [role="combobox"], [data-testid="stMultiSelect"] [role="combobox"] { background: #fff !important; border: 0 !important; outline: 0 !important; color: #173d46 !important; -webkit-text-fill-color: #173d46 !important; box-shadow: none !important; }
          [data-testid="stSelectbox"] [role="group"] button[aria-label="Open"], [data-testid="stMultiSelect"] [role="group"] button[aria-label="Open"] { background: transparent !important; border: 0 !important; color: #496b72 !important; box-shadow: none !important; }
          [data-testid="stSelectbox"] [role="group"] svg, [data-testid="stMultiSelect"] [role="group"] svg { color: #496b72 !important; fill: #496b72 !important; }
          [data-testid="stMultiSelect"] [data-baseweb="tag"] { background: #dff3ef !important; border: 1px solid #b9e1d8 !important; color: #17695f !important; }
          [data-testid="stMultiSelect"] [data-baseweb="tag"] * { color: #17695f !important; }
          [data-testid="stSelectbox"] svg, [data-testid="stMultiSelect"] svg { color: #496b72 !important; fill: #496b72 !important; }
          [data-testid="stTextInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder, [data-testid="stMultiSelect"] input::placeholder { color: #718990 !important; -webkit-text-fill-color: #718990 !important; opacity: 1 !important; }
          div[data-testid="stMetric"] { background: linear-gradient(145deg, #fff, #f0f8f8) !important; box-shadow: inset 0 1px #fff, 0 8px 26px rgba(38,91,98,.08) !important; }
          div[data-testid="stMetricValue"] { color: #173d46 !important; }
          div[data-testid="stAlert"] { color: #254c53 !important; }
          .stButton button { background: rgba(255,255,255,.76) !important; color: #294e55 !important; border-color: rgba(44,106,113,.22) !important; }
          div[data-testid="stFormSubmitButton"] button { color: #06372f !important; -webkit-text-fill-color: #06372f !important; background: linear-gradient(135deg, #62d8bf, #28a991) !important; border-color: rgba(24,125,107,.38) !important; }
          div[data-testid="stFormSubmitButton"] button:disabled { color: #174c45 !important; -webkit-text-fill-color: #174c45 !important; opacity: 1 !important; }
          [data-testid="stDialog"] > div { background: linear-gradient(145deg, #f8fdfc, #e9f4f3 82%) !important; border-color: rgba(32,121,111,.22) !important; }
          [data-testid="stDialog"] h2 { color: #173d46 !important; }
          .key-connect-visual { background: radial-gradient(ellipse at 22% 50%, rgba(48,184,161,.12), transparent 56%), rgba(255,255,255,.78) !important; border-color: rgba(39,126,117,.18) !important; }
          .key-connect-copy strong { color: #173d46 !important; }
          .key-connect-copy p { color: #506a70 !important; }
          .key-security-note { color: #5b4b29 !important; background: #fff5dc !important; border-color: rgba(202,148,48,.24) !important; }
          [data-testid="stExpander"] { border-color: rgba(43,101,108,.2) !important; }
          [data-testid="stTabs"] button[aria-selected="true"] { color: #138b7e !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

HERO_VISUAL_HTML = """
<div class="hero-visual-shell">
  <div class="hero-visual">
    <div class="hero-visual-label">MEDIGUIDE / HEALTH AI</div>
    <div class="hero-visual-status"><i></i> EDUCATIONAL MODE</div>
    <div class="orb-stage" aria-hidden="true">
      <div class="orb-halo"></div>
      <div class="orb-core"></div>
      <div class="orb-ring"></div>
      <div class="orb-ring orb-ring-secondary"></div>
    </div>
    <div class="hero-visual-foot">
      <div><strong>Structured guidance</strong><small>Built around cautious, clear next steps</small></div>
      <span class="orbit-mark">✳</span>
    </div>
  </div>
</div>
"""


def get_chat_model(model_name: str, api_key: str):
    """Build a model client without caching visitor-provided credentials globally."""
    return create_chat_model(model_name, api_key)


@st.dialog("Connect to MediGuide", width="medium", dismissible=False, icon=":material/key:")
def api_key_dialog(server_key_available: bool) -> None:
    """Collect an optional visitor key for this Streamlit session only."""
    st.markdown(
        '<div class="key-connect-visual">'
        '<div class="key-orb-scene"><div class="key-orb"></div><div class="key-orbit"></div></div>'
        '<div class="key-connect-copy"><strong>Your session, your connection</strong>'
        '<p>Add your OpenAI API key for this session, or use the app connection if one is configured.</p></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="key-security-note">A personal key travels from your browser to this app host and is then used with OpenAI. '
        'Only enter it on a deployment you trust. MediGuide keeps it in the active Streamlit session memory; it is not written to a file or GitHub. '
        'Using a personal key turns caching off for your requests.</div>',
        unsafe_allow_html=True,
    )
    with st.form("visitor_api_key_form"):
        candidate_key = st.text_input(
            "OpenAI API key",
            type="password",
            placeholder="Paste your key for this session",
            key="visitor_api_key_input",
        )
        connect_clicked = st.form_submit_button(
            "Connect for this session",
            type="primary",
            use_container_width=True,
        )
    if connect_clicked:
        if candidate_key.strip():
            st.session_state.visitor_api_key = candidate_key.strip()
            st.session_state.api_key_dialog_dismissed = True
            st.rerun()
        else:
            st.error("Paste an API key, or continue without AI guidance.")

    if server_key_available and st.button("Continue with the app connection", use_container_width=True):
        st.session_state.pop("visitor_api_key", None)
        st.session_state.api_key_dialog_dismissed = True
        st.rerun()

    if st.button("Continue without an API key", use_container_width=True):
        st.session_state.api_key_dialog_dismissed = True
        st.rerun()


def _patient_prompt_data(patient: dict[str, object], language: str) -> str:
    return ASSESSMENT_PROMPT_TEMPLATE.format(
        age=patient["age"],
        gender=patient["gender"],
        symptoms=patient["symptoms"],
        duration=patient["duration"],
        severity=patient["severity"],
        conditions=patient["conditions"] or "Not provided",
        medications=patient["medications"] or "Not provided",
        notes=patient["notes"] or "Not provided",
        language=language,
    )


def _get_result_cache() -> dict[str, dict[str, object]]:
    if "result_cache" not in st.session_state:
        st.session_state.result_cache = {}
    return st.session_state.result_cache


def _stream_and_store_narrative(llm, assessment: dict[str, object], raw_json: str) -> str:
    with st.container(border=True):
        st.markdown("#### Live plain-language guidance")
        filter_state = {"blocked": False}
        try:
            streamed = st.write_stream(
                stream_narrative(
                    llm,
                    assessment_json=raw_json,
                    language=st.session_state.get("answer_language", "English"),
                    on_filtered=lambda: filter_state.__setitem__("blocked", True),
                )
            )
            if filter_state["blocked"]:
                st.caption(
                    "A safety filter withheld model text containing medication advice or a specific threshold."
                )
            return streamed if isinstance(streamed, str) else ""
        except Exception as exc:  # Keep the structured result available if narration fails.
            st.warning(
                "The structured result is available, but live narration could not be "
                "completed. The model may be temporarily unavailable."
            )
            st.caption(f"Streaming detail: {exc}")
            return str(assessment.get("summary", ""))


def _render_disclaimer(sidebar: bool = False) -> None:
    banner = (
        '<div class="safety-banner"><span class="safety-banner-mark">!</span>'
        '<div><strong>Educational use only</strong>'
        f'<p>{SAFETY_DISCLAIMER}</p></div></div>'
    )
    if sidebar:
        st.sidebar.markdown(banner, unsafe_allow_html=True)
    else:
        st.markdown(banner, unsafe_allow_html=True)


def _render_result(result: dict[str, object]) -> None:
    st.divider()
    st.header("Guidance dashboard")
    _render_disclaimer()

    if result.get("error"):
        st.error(str(result["error"]))
        raw = result.get("raw_response")
        if raw:
            with st.expander("Raw model output for debugging"):
                st.code(str(raw), language="text")
        return

    assessment = result["assessment"]
    assert isinstance(assessment, dict)
    urgency = str(assessment["urgency_level"])
    if urgency == "EMERGENCY":
        st.error(
            "Emergency warning: seek local emergency help immediately. Do not wait for this app."
        )
    else:
        st.success("General educational information is ready. Review it with a qualified professional.")

    css_class = f"urgency-{urgency.lower()}"
    st.markdown(
        f'<span class="urgency-chip {css_class}">{urgency}</span>',
        unsafe_allow_html=True,
    )

    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Urgency estimate", urgency)
    metric_b.metric("Reported severity", f"{result['severity']}/10")
    metric_c.metric("Symptoms entered", str(result["symptom_count"]))

    narrative = str(result.get("narrative", ""))
    if narrative:
        with st.expander("Streamed plain-language guidance", expanded=True):
            st.write(narrative)

    st.subheader("Patient symptom summary")
    st.write(assessment["summary"])

    if result.get("cache_hit"):
        st.caption("Repeated identical request served from this session's result cache.")
    elif result.get("cache_mode") in {"In-memory", "SQLite"}:
        st.caption(f"LangChain model cache mode: {result['cache_mode']}.")

    tab_summary, tab_next, tab_questions, tab_warnings = st.tabs(
        ["Possible conditions", "Next steps", "Ask a professional", "Warning signs"]
    )
    with tab_summary:
        st.caption("Education only; these are possibilities, not a diagnosis.")
        conditions = assessment["possible_conditions"]
        if conditions:
            for item in conditions:
                st.markdown(f"**{item['name']}**")
                st.write(item["reason"])
        else:
            st.write("No possible conditions were returned.")
    with tab_next:
        for item in assessment["recommended_next_steps"]:
            st.markdown(f"- {item}")
        if not assessment["recommended_next_steps"]:
            st.write("Follow up with a qualified healthcare professional for personal advice.")
    with tab_questions:
        for item in assessment["questions_for_doctor"]:
            st.markdown(f"- {item}")
        if not assessment["questions_for_doctor"]:
            st.write("No questions were returned.")
    with tab_warnings:
        for item in assessment["warning_signs"]:
            st.markdown(f"- {item}")
        if not assessment["warning_signs"]:
            st.write("If symptoms become severe or worsen, seek professional care promptly.")

    if result.get("raw_response"):
        with st.expander("Structured JSON response (assignment view)"):
            st.code(str(result["raw_response"]), language="json")


def _process_submission(
    patient: dict[str, object],
    model_name: str,
    language: str,
    cache_mode: str,
) -> None:
    symptoms = patient["symptoms"]
    assert isinstance(symptoms, list)
    notes = str(patient["notes"])
    cache_key = make_cache_key(patient, model_name, language)
    result_cache = _get_result_cache()
    visitor_api_key = str(st.session_state.get("visitor_api_key", "")).strip()
    api_key = visitor_api_key or get_server_api_key()
    active_cache_mode = "Off" if visitor_api_key else cache_mode

    if detect_emergency(symptoms, notes):
        assessment = emergency_assessment(language)
        raw_json = json.dumps(assessment, ensure_ascii=False, indent=2)
        narrative = " ".join(
            [str(assessment["summary"]), *assessment["recommended_next_steps"]]
        )
        with st.container(border=True):
            st.markdown("#### Immediate safety message")
            st.write_stream(stream_text_chunks(narrative))
        st.session_state.last_result = {
            "assessment": assessment,
            "raw_response": raw_json,
            "narrative": narrative,
            "severity": patient["severity"],
            "symptom_count": len(symptoms),
            "cache_mode": active_cache_mode,
            "cache_hit": False,
            "emergency": True,
        }
        return

    if not api_key or api_key == "replace-with-your-own-key":
        st.session_state.last_result = {
            "error": "No API key is connected. Use the sidebar's API key button to add a session key, or configure OPENAI_API_KEY for the app.",
            "severity": patient["severity"],
            "symptom_count": len(symptoms),
        }
        return

    if active_cache_mode != "Off" and cache_key in result_cache:
        cached = result_cache[cache_key]
        with st.container(border=True):
            st.markdown("#### Cached plain-language guidance")
            st.write_stream(stream_text_chunks(str(cached["narrative"])))
        st.session_state.last_result = {
            **cached,
            "cache_mode": active_cache_mode,
            "cache_hit": True,
        }
        return

    try:
        with llm_cache_context(active_cache_mode, DEFAULT_CACHE_PATH):
            llm = get_chat_model(model_name, api_key)
            chain = build_assessment_chain(llm)
            prompt_inputs = {"patient_details": _patient_prompt_data(patient, language)}
            with st.spinner("Preparing the structured educational response…"):
                chain_result = chain.invoke(prompt_inputs)
            raw_response = str(chain_result["assessment_json"])
            if contains_unsafe_medical_advice(raw_response):
                raise UnsafeMedicalOutputError(
                    "The model response included medication advice or a specific medical threshold."
                )
            assessment = parse_assessment(raw_response)
            narrative = _stream_and_store_narrative(llm, assessment, raw_response)
    except UnsafeMedicalOutputError:
        st.session_state.last_result = {
            "error": (
                "The model response included medication advice or a specific medical "
                "threshold, so it was blocked. Please try again or consult a qualified professional."
            ),
            "severity": patient["severity"],
            "symptom_count": len(symptoms),
        }
        return
    except Exception as exc:
        st.session_state.last_result = {
            "error": (
                "The guidance request could not be completed. Check the API key, "
                "model access, and internet connection, then try again."
            ),
            "raw_response": locals().get("raw_response"),
            "detail": str(exc),
            "severity": patient["severity"],
            "symptom_count": len(symptoms),
        }
        return

    result = {
        "assessment": assessment,
        "raw_response": raw_response,
        "narrative": narrative,
        "severity": patient["severity"],
        "symptom_count": len(symptoms),
        "cache_mode": active_cache_mode,
        "cache_hit": False,
        "emergency": False,
    }
    if active_cache_mode != "Off":
        result_cache[cache_key] = result
    st.session_state.last_result = result


st.sidebar.title("🩺 MediGuide AI")
st.sidebar.caption(APP_SUBTITLE)
_render_disclaimer(sidebar=True)
st.sidebar.toggle("Day theme", key="day_mode", help="On = Day appearance. Off = Night appearance.")

server_api_key = get_server_api_key()
visitor_api_key = str(st.session_state.get("visitor_api_key", "")).strip()
if visitor_api_key:
    st.sidebar.success("Personal API key connected for this session.")
elif server_api_key:
    st.sidebar.info("App-configured API connection is available.")
else:
    st.sidebar.caption("No API key connected yet. Emergency guidance remains available.")
if st.sidebar.button("Connect or change API key", use_container_width=True):
    st.session_state.api_key_dialog_dismissed = False
    st.rerun()

st.sidebar.subheader("Model configuration")
env_model = DEFAULT_MODEL if DEFAULT_MODEL in MODEL_OPTIONS else MODEL_OPTIONS[0]
model_name = st.sidebar.selectbox(
    "OpenAI model",
    MODEL_OPTIONS,
    index=MODEL_OPTIONS.index(env_model),
    help="The model name can also be changed with OPENAI_MODEL in your local .env file.",
)
language = st.sidebar.selectbox("Answer language", LANGUAGE_OPTIONS, index=0)
st.session_state.answer_language = language
if visitor_api_key:
    cache_mode = "Off"
    st.sidebar.info("Caching is off while you use a personal session key.")
else:
    cache_mode = st.sidebar.selectbox(
        "Model cache",
        CACHE_OPTIONS,
        index=0,
        help="Off is safest for privacy. Cache modes are for this educational prototype.",
    )

try:
    configure_llm_cache(cache_mode, DEFAULT_CACHE_PATH)
except Exception as exc:
    st.sidebar.error(f"Could not configure the selected cache: {exc}")
    cache_mode = "Off"
    configure_llm_cache("Off", DEFAULT_CACHE_PATH)

if not visitor_api_key and cache_mode == "SQLite":
    st.sidebar.warning(
        "SQLiteCache stores model prompts and replies in a local database file. "
        "Do not enter identifying or real patient information."
    )
elif not visitor_api_key and cache_mode == "In-memory":
    st.sidebar.info("In-memory cache stays in the running app process and is lost when it stops.")
elif not visitor_api_key:
    st.sidebar.info("Model caching is off. Identical submissions may call the model again.")

if st.sidebar.button("Clear selected model cache", disabled=(cache_mode == "Off")):
    if clear_active_cache():
        _get_result_cache().clear()
        st.sidebar.success("The selected model cache was cleared.")
    else:
        st.sidebar.info("No active cache to clear.")

st.sidebar.caption(
    "Only fictional/demo information should be entered. Non-emergency entries are sent "
    "to the configured OpenAI API. This prototype is not for real patient care."
)

if not st.session_state.get("api_key_dialog_dismissed", False):
    api_key_dialog(server_key_available=bool(server_api_key))

hero_copy, hero_visual = st.columns([1.25, .85], gap="large", vertical_alignment="center")
with hero_copy:
    st.markdown(
        '<div class="hero-copy-block">'
        '<div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span> LangChain · Streamlit · OpenAI</div>'
        '<h1>Understand your symptoms.<br><span>Find a clearer next step.</span></h1>'
        '<p>MediGuide turns a few details into structured, cautious health information for learning and demonstration.</p>'
        '<div class="hero-meta"><span>Educational prototype</span><span>English + Urdu</span><span>No confirmed diagnosis</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )
with hero_visual:
    st.markdown(HERO_VISUAL_HTML, unsafe_allow_html=True)

st.markdown('<div class="section-eyebrow">01 / Patient intake</div>', unsafe_allow_html=True)
_render_disclaimer()

with st.form("patient_information", clear_on_submit=False):
    st.subheader("Patient information")
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        age_text = st.text_input("Age", placeholder="Whole years")
    with col_b:
        gender = st.selectbox("Gender", GENDER_OPTIONS)
    with col_c:
        duration = st.selectbox("Symptom duration", DURATION_OPTIONS)

    symptoms = st.multiselect(
        "Symptoms",
        SYMPTOM_OPTIONS,
        help="Select all that apply. Add a brief description below if needed.",
    )
    free_text_symptoms = st.text_area(
        "Additional symptom details",
        placeholder="Optional. Do not include names, contact details, or other identifying information.",
        height=80,
    )
    severity = st.slider("Overall severity (self-reported)", min_value=1, max_value=10, value=3)

    col_d, col_e = st.columns(2)
    with col_d:
        conditions = st.text_area("Existing medical conditions", height=100)
        medications = st.text_area("Current medications", height=100)
    with col_e:
        notes = st.text_area("Additional notes", height=100)
        st.caption("Do not enter names, addresses, phone numbers, or real patient identifiers.")

    submitted = st.form_submit_button("Generate educational guidance", type="primary", use_container_width=True)

if st.button("Clear displayed result"):
    st.session_state.pop("last_result", None)

if submitted:
    st.session_state.pop("last_result", None)
    age, age_error = validate_age(age_text)
    symptoms_all = [item for item in symptoms if item != "Other"]
    if free_text_symptoms.strip():
        symptoms_all.append(free_text_symptoms.strip())

    if not symptoms_all:
        st.warning("Enter or select at least one symptom. No API call was made.")
    elif age_error and not detect_emergency(symptoms_all, notes.strip()):
        st.warning(age_error)
    else:
        patient = {
            "age": age,
            "gender": gender,
            "symptoms": symptoms_all,
            "duration": duration,
            "severity": severity,
            "conditions": conditions.strip(),
            "medications": medications.strip(),
            "notes": notes.strip(),
        }
        _process_submission(patient, model_name, language, cache_mode)

last_result = st.session_state.get("last_result")
if last_result:
    _render_result(last_result)

with st.expander("How the LangChain message roles fit together"):
    st.caption(
        "SystemMessage provides rules, HumanMessage carries user input, and AIMessage "
        "represents an earlier assistant reply in conversation history. The example below is fictional."
    )
    for message in demonstrate_message_roles():
        st.markdown(f"**{message.type.title()}Message**")
        st.code(str(message.content), language="text")

st.caption("MediGuide AI is an educational software prototype, not a medical device.")

