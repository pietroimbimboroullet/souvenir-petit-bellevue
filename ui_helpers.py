"""
ui_helpers.py — UI theming condiviso per tutte le pagine Streamlit.
Logo (sidebar aperta/chiusa) + CSS custom.
Palette allineata a Bellevue Schedule: cream/sage/earth + JetBrains Mono + Playfair Display.
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
/* ══════════════════════════════════════════════════════════════
   SOUVENIR PETIT BELLEVUE — Design System
   Palette: Bellevue Schedule (cream / sage / earth)
   Fonts: JetBrains Mono (dati) + Playfair Display (headings)
   ══════════════════════════════════════════════════════════════ */

/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap');

/* ── Body background ── */
.stApp, [data-testid="stAppViewContainer"] {
    background-color: #faf7f3 !important;
}

/* ── Titoli: Playfair Display ── */
h1, h2, h3 {
    font-family: 'Playfair Display', Georgia, serif !important;
    letter-spacing: 0.01em;
    color: #4a6340 !important;
}
h1 { font-weight: 700 !important; }
h2, h3 { font-weight: 600 !important; }

/* ── Captions under titles ── */
.title-caption {
    font-family: 'Playfair Display', Georgia, serif;
    font-style: italic;
    color: #96816a;
    margin-top: -0.8rem;
    margin-bottom: 1.5rem;
    font-size: 1.05rem;
}

/* ── Sidebar: cream + dashed border ── */
section[data-testid="stSidebar"] {
    background: #faf7f3 !important;
    border-right: 1px dashed #d4c4b0 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 1.5rem;
}

/* ── Header ── */
header[data-testid="stHeader"] {
    background: rgba(250, 247, 243, 0.95);
    backdrop-filter: blur(8px);
}

/* ── Primary buttons: sage solid ── */
button[kind="primary"],
.stButton > button[kind="primary"] {
    background: #5f7d52 !important;
    border: none !important;
    color: #fff !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.12s ease !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}
button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover {
    background: #4a6340 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important;
}

/* ── Secondary buttons: dashed cream border ── */
button[kind="secondary"],
.stButton > button[kind="secondary"] {
    border: 1px dashed #d4c4b0 !important;
    border-radius: 8px !important;
    background: #faf7f3 !important;
    color: #96816a !important;
    font-weight: 500 !important;
    transition: all 0.12s ease !important;
}
button[kind="secondary"]:hover,
.stButton > button[kind="secondary"]:hover {
    border-color: #7c9a6e !important;
    color: #4a6340 !important;
    background: #e8f0e4 !important;
}

/* ── Download buttons: dashed sage border ── */
.stDownloadButton > button {
    border: 2px dashed #7c9a6e !important;
    border-radius: 8px !important;
    color: #4a6340 !important;
    background: transparent !important;
    font-weight: 600 !important;
    transition: all 0.12s ease !important;
}
.stDownloadButton > button:hover {
    background: #e8f0e4 !important;
    transform: translateY(-1px) !important;
}

/* ── Expanders: dashed border + cream bg ── */
.streamlit-expanderHeader {
    border-radius: 10px !important;
    font-family: 'Playfair Display', Georgia, serif !important;
    font-weight: 600 !important;
    color: #4a6340 !important;
}
details[data-testid="stExpander"] {
    border-radius: 10px !important;
    border: 1px dashed #d4c4b0 !important;
    background: #faf7f3 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    transition: all 0.12s ease !important;
}
details[data-testid="stExpander"]:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
    border-color: #9dbc8e !important;
}

/* ── Container cards: dashed border ── */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"][data-has-border="true"]) {
    border-radius: 10px !important;
    border: 1px dashed #d4c4b0 !important;
    transition: all 0.12s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"][data-has-border="true"]):hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}

/* ── Tabs: serif font, sage underline ── */
.stTabs [data-baseweb="tab"] {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: #96816a !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #4a6340 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #5f7d52 !important;
}

/* ── Metrics: JetBrains Mono per valori, sage tinted card ── */
[data-testid="stMetric"] {
    background: #e8f0e4;
    border: 1px dashed #d4c4b0;
    border-radius: 10px;
    padding: 0.75rem 1rem;
}
[data-testid="stMetricLabel"] {
    color: #96816a !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
[data-testid="stMetricValue"] {
    color: #4a6340 !important;
    font-weight: 700 !important;
}

/* ── Input fields: rounded, dashed border ── */
.stTextInput input,
.stNumberInput input,
.stDateInput input {
    border: 1px dashed #d4c4b0 !important;
    border-radius: 6px !important;
    background: #faf7f3 !important;
    transition: border-color 0.12s ease !important;
}
.stTextInput input:focus,
.stNumberInput input:focus,
.stDateInput input:focus {
    border-color: #7c9a6e !important;
}

.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"] {
    border-radius: 6px !important;
}

/* ── Dividers: softer cream dashed ── */
hr {
    border-color: #d4c4b0 !important;
    border-style: dashed !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
}

/* ── Max width for comfortable reading ── */
.block-container {
    max-width: 1100px !important;
}

/* ── Scrollbar: cream/earth ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f5f0eb; }
::-webkit-scrollbar-thumb { background: #d4c4b0; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #b8a48e; }

/* ── Hide Streamlit branding ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ── Form submit buttons ── */
[data-testid="stFormSubmitButton"] > button {
    border-radius: 8px !important;
}

/* ── Icon-only action buttons — center in column ── */
[data-testid="stHorizontalBlock"] [data-testid="stColumn"] .stButton > button {
    min-width: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}
[data-testid="stVerticalBlock"][data-has-border="true"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
</style>
"""
