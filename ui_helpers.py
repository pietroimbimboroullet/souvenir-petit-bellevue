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
   Fonts: JetBrains Mono (body) + Playfair Display (headings)
   ══════════════════════════════════════════════════════════════ */

/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap');

/* ── CSS Variables (Bellevue Schedule palette) ── */
:root {
    --cream-50:  #faf7f3;
    --cream-100: #f5f0eb;
    --cream-200: #ebe3d9;
    --cream-300: #d4c4b0;
    --cream-400: #bfa98f;

    --sage-100:  #e8f0e4;
    --sage-200:  #c5d9bc;
    --sage-300:  #9dbc8e;
    --sage-400:  #7c9a6e;
    --sage-500:  #5f7d52;
    --sage-600:  #4a6340;

    --earth-100: #f0e6d8;
    --earth-200: #e0d2c2;
    --earth-300: #d4c4b0;
    --earth-400: #b8a48e;
    --earth-500: #96816a;

    --text-dark: #3a3530;

    --font-mono:  'JetBrains Mono', monospace;
    --font-serif: 'Playfair Display', Georgia, serif;
}

/* ── Global font: JetBrains Mono ── */
html, body, [class*="st-"],
.stApp, .stMarkdown, .stText,
p, span, li, label, input, textarea, select, option,
div[data-testid="stMetricValue"],
div[data-testid="stMetricDelta"] {
    font-family: var(--font-mono) !important;
    color: var(--text-dark);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* ── Body background ── */
.stApp, [data-testid="stAppViewContainer"] {
    background-color: var(--cream-50) !important;
}

/* ── Titoli: Playfair Display ── */
h1, h2, h3 {
    font-family: var(--font-serif) !important;
    letter-spacing: 0.01em;
    color: var(--sage-600) !important;
}
h1 { font-weight: 700 !important; }
h2, h3 { font-weight: 600 !important; }

/* ── Captions under titles ── */
.title-caption {
    font-family: var(--font-serif);
    font-style: italic;
    color: var(--earth-500);
    margin-top: -0.8rem;
    margin-bottom: 1.5rem;
    font-size: 1.05rem;
}

/* ── Sidebar: cream gradient + dashed border ── */
section[data-testid="stSidebar"] {
    background: var(--cream-50) !important;
    border-right: 1px dashed var(--cream-300) !important;
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
    background: var(--sage-500) !important;
    border: none !important;
    color: #fff !important;
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    transition: all 0.12s ease !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}
button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover {
    background: var(--sage-600) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important;
}

/* ── Secondary buttons: dashed cream border ── */
button[kind="secondary"],
.stButton > button[kind="secondary"] {
    border: 1px dashed var(--cream-300) !important;
    border-radius: 8px !important;
    background: var(--cream-50) !important;
    color: var(--earth-500) !important;
    font-family: var(--font-mono) !important;
    font-weight: 500 !important;
    transition: all 0.12s ease !important;
}
button[kind="secondary"]:hover,
.stButton > button[kind="secondary"]:hover {
    border-color: var(--sage-400) !important;
    color: var(--sage-600) !important;
    background: var(--sage-100) !important;
}

/* ── Download buttons: dashed sage border ── */
.stDownloadButton > button {
    border: 2px dashed var(--sage-400) !important;
    border-radius: 8px !important;
    color: var(--sage-600) !important;
    background: transparent !important;
    font-family: var(--font-mono) !important;
    font-weight: 600 !important;
    transition: all 0.12s ease !important;
}
.stDownloadButton > button:hover {
    background: var(--sage-100) !important;
    transform: translateY(-1px) !important;
}

/* ── Expanders: dashed border + cream bg ── */
.streamlit-expanderHeader {
    border-radius: 10px !important;
    font-family: var(--font-serif) !important;
    font-weight: 600 !important;
    color: var(--sage-600) !important;
}
details[data-testid="stExpander"] {
    border-radius: 10px !important;
    border: 1px dashed var(--cream-300) !important;
    background: var(--cream-50) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    transition: all 0.12s ease !important;
}
details[data-testid="stExpander"]:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
    border-color: var(--sage-300) !important;
}

/* ── Container cards: dashed border ── */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"][data-has-border="true"]) {
    border-radius: 10px !important;
    border: 1px dashed var(--cream-300) !important;
    transition: all 0.12s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"][data-has-border="true"]):hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}

/* ── Tabs: serif font, sage underline ── */
.stTabs [data-baseweb="tab"] {
    font-family: var(--font-serif) !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: var(--earth-500) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--sage-600) !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: var(--sage-500) !important;
}

/* ── Metrics: sage tinted card ── */
[data-testid="stMetric"] {
    background: var(--sage-100);
    border: 1px dashed var(--cream-300);
    border-radius: 10px;
    padding: 0.75rem 1rem;
}
[data-testid="stMetricLabel"] {
    color: var(--earth-500) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
[data-testid="stMetricValue"] {
    color: var(--sage-600) !important;
    font-weight: 700 !important;
}

/* ── Input fields: rounded, dashed border ── */
.stTextInput input,
.stNumberInput input,
.stDateInput input {
    border: 1px dashed var(--cream-300) !important;
    border-radius: 6px !important;
    font-family: var(--font-mono) !important;
    background: var(--cream-50) !important;
    transition: border-color 0.12s ease !important;
}
.stTextInput input:focus,
.stNumberInput input:focus,
.stDateInput input:focus {
    border-color: var(--sage-400) !important;
}

.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"] {
    border-radius: 6px !important;
    font-family: var(--font-mono) !important;
}

/* ── Dividers: softer cream ── */
hr {
    border-color: var(--cream-300) !important;
    border-style: dashed !important;
}

/* ── Success/Warning/Error: tinted ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
}

/* ── Max width for comfortable reading ── */
.block-container {
    max-width: 1100px !important;
}

/* ── Scrollbar: cream/earth (Bellevue Schedule) ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--cream-100); }
::-webkit-scrollbar-thumb { background: var(--cream-300); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--earth-400); }

/* ── Hide Streamlit branding ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ── Form submit buttons ── */
[data-testid="stFormSubmitButton"] > button {
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
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

/* ── Data editor: mono font ── */
[data-testid="stDataEditor"] {
    font-family: var(--font-mono) !important;
}
</style>
"""
