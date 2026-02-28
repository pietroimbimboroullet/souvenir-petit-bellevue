"""
ui_helpers.py — UI theming condiviso per tutte le pagine Streamlit.
Logo (sidebar aperta/chiusa) + CSS custom.
"""

from pathlib import Path
import streamlit as st

_ASSETS = Path(__file__).resolve().parent / "assets"


def apply_ui():
    """Chiama dopo st.set_page_config(). Inietta logo + CSS."""

    # ── Logo ──
    logo_path = _ASSETS / "logo.png"
    icon_path = _ASSETS / "logo_icon.png"
    if logo_path.exists() and icon_path.exists():
        st.logo(
            image=str(logo_path),
            icon_image=str(icon_path),
            size="large",
        )

    # ── CSS ──
    st.markdown(_CSS, unsafe_allow_html=True)


_CSS = """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap');

/* ── Titoli serif ── */
h1, h2, h3 {
    font-family: 'Playfair Display', Georgia, serif !important;
    letter-spacing: 0.01em;
}
h1 { font-weight: 700 !important; }
h2, h3 { font-weight: 600 !important; }

/* ── Sidebar gradient ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FAF8F5 0%, #F0EDE8 100%);
}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 1.5rem;
}

/* ── Primary buttons: sage green gradient ── */
button[kind="primary"],
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6B7F6B 0%, #7A8F7A 100%) !important;
    border: none !important;
    color: #fff !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 4px rgba(107,127,107,0.2) !important;
}
button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(107,127,107,0.35) !important;
}

/* ── Secondary buttons ── */
button[kind="secondary"],
.stButton > button[kind="secondary"] {
    border-radius: 8px !important;
    border-color: #C8C0B4 !important;
    transition: all 0.2s ease !important;
}
button[kind="secondary"]:hover,
.stButton > button[kind="secondary"]:hover {
    border-color: #6B7F6B !important;
    color: #6B7F6B !important;
}

/* ── Download buttons: dashed sage border ── */
.stDownloadButton > button {
    border: 2px dashed #6B7F6B !important;
    border-radius: 8px !important;
    color: #6B7F6B !important;
    background: transparent !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    background: rgba(107,127,107,0.06) !important;
    transform: translateY(-1px) !important;
}

/* ── Expanders: rounded + subtle shadow ── */
.streamlit-expanderHeader {
    border-radius: 10px !important;
    font-family: 'Playfair Display', Georgia, serif !important;
    font-weight: 600 !important;
}
details[data-testid="stExpander"] {
    border-radius: 10px !important;
    border-color: #E0D8CE !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
    transition: box-shadow 0.2s ease !important;
}
details[data-testid="stExpander"]:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}

/* ── Container cards: hover shadow ── */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"][data-has-border="true"]) {
    border-radius: 10px !important;
    transition: box-shadow 0.2s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"][data-has-border="true"]):hover {
    box-shadow: 0 2px 10px rgba(0,0,0,0.06) !important;
}

/* ── Tabs: serif font ── */
.stTabs [data-baseweb="tab"] {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
}

/* ── Metrics: sage background ── */
[data-testid="stMetric"] {
    background: rgba(107,127,107,0.06);
    border-radius: 10px;
    padding: 0.75rem 1rem;
}

/* ── Input fields: rounded ── */
.stTextInput input,
.stNumberInput input,
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"],
.stDateInput input {
    border-radius: 6px !important;
}

/* ── Max width for comfortable reading ── */
.block-container {
    max-width: 1100px !important;
}

/* ── Hide Streamlit branding ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {
    background: rgba(250,250,248,0.95);
    backdrop-filter: blur(8px);
}

/* ── Captions under titles ── */
.title-caption {
    font-family: 'Playfair Display', Georgia, serif;
    font-style: italic;
    color: #8B8070;
    margin-top: -0.8rem;
    margin-bottom: 1.5rem;
    font-size: 1.05rem;
}

/* ── Dividers: softer ── */
hr {
    border-color: #E8E0D8 !important;
}

/* ── Form submit buttons ── */
[data-testid="stFormSubmitButton"] > button {
    border-radius: 8px !important;
}
</style>
"""
