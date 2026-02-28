"""
app.py — Interfaccia Streamlit per Souvenir Petit Bellevue
Tavolo-centrica: 5 tavoli sempre visibili, configurazione ospiti inline.
"""

import io, zipfile, sys
from pathlib import Path
from datetime import date

import streamlit as st
import fitz  # PyMuPDF

# ── Percorsi ──
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

from genera_souvenir import (
    genera_souvenir, safe_filename, get_db, set_db, OUTPUT_DIR,
)

# ── Caricamento DB (Supabase con fallback JSON) ──
try:
    from supabase_utils import load_db
    _db = load_db()
except Exception:
    _db = None

if _db:
    set_db(_db)

DB = get_db()

# ── Configurazione tavoli ──
TAVOLI = [
    ("1pb", 2),
    ("3pb", 2),
    ("4pb", 2),
    ("5pb", 6),
    ("6pb", 4),
]

LINGUE = ["it", "fr", "en"]
TIPI_MENU = ["esprit", "terroir", "carta"]

# Piatti leggibili dal database (id -> nome_it)
PIATTI_MAP = {p["id"]: f'{p["nome_it"]} — {p["ingredienti_it"]}' for p in DB["piatti"]}
PIATTI_IDS = list(PIATTI_MAP.keys())

# ══════════════════════════════════════════════════════════════
st.set_page_config(page_title="Souvenir Petit Bellevue", layout="wide")
st.title("Souvenir Petit Bellevue")

# ── Sidebar ──
with st.sidebar:
    data_serata = st.date_input("Data serata", value=date.today())
    st.divider()
    btn_genera = st.button("Genera tutti i PDF", type="primary", use_container_width=True)
    placeholder_download = st.empty()
    placeholder_stats = st.empty()

# ── Stato ospiti (session_state) ──
if "pdfs" not in st.session_state:
    st.session_state.pdfs = []  # lista di (label, filename, bytes)

# ══════════════════════════════════════════════════════════════
# AREA PRINCIPALE — 5 tavoli
# ══════════════════════════════════════════════════════════════

def raccolta_ordini():
    """Legge i widget e ritorna lista di dict ordini da generare."""
    ordini = []
    for tav, max_osp in TAVOLI:
        n = st.session_state.get(f"n_{tav}", 0)
        for i in range(1, n + 1):
            k = f"{tav}_{i}"
            nome = st.session_state.get(f"nome_{k}", "").strip() or f"Ospite_{i}"
            lingua = st.session_state.get(f"lingua_{k}", "it")
            tipo_menu = st.session_state.get(f"menu_{k}", "esprit")

            # Piatti (solo carta)
            piatti_csv = ""
            if tipo_menu == "carta":
                sel = st.session_state.get(f"piatti_{k}", [])
                if not sel:
                    st.warning(f"Tavolo {tav}, {nome}: nessun piatto selezionato — saltato")
                    continue
                piatti_csv = ", ".join(sel)

            ordini.append(dict(
                tavolo=tav, nome=nome, lingua=lingua,
                tipo_menu=tipo_menu, piatti_csv=piatti_csv,
                numero_ospite=i,
            ))
    return ordini


# ── Render tavoli ──
tot_ospiti = 0
tot_tavoli_attivi = 0

for tav, max_osp in TAVOLI:
    with st.expander(f"Tavolo {tav}  (max {max_osp})", expanded=True):
        n = st.selectbox(
            "Ospiti", range(0, max_osp + 1), key=f"n_{tav}",
            label_visibility="collapsed",
            format_func=lambda x: f"{x} ospiti" if x != 1 else "1 ospite",
        )
        if n > 0:
            tot_ospiti += n
            tot_tavoli_attivi += 1

        for i in range(1, n + 1):
            k = f"{tav}_{i}"
            st.markdown(f"**Ospite {i}**")
            c1, c2 = st.columns([2, 1])
            with c1:
                st.text_input("Nome (opz.)", key=f"nome_{k}", placeholder=f"Ospite_{i}")
            with c2:
                st.selectbox("Lingua", LINGUE, key=f"lingua_{k}")

            tipo_menu = st.selectbox("Menu", TIPI_MENU, key=f"menu_{k}")

            # Piatti (solo carta)
            if tipo_menu == "carta":
                st.multiselect(
                    "Piatti",
                    options=PIATTI_IDS,
                    format_func=lambda x: PIATTI_MAP.get(x, x),
                    key=f"piatti_{k}",
                )

            if i < n:
                st.divider()

# ── Stats sidebar ──
placeholder_stats.metric("Coperti", f"{tot_ospiti} ospiti, {tot_tavoli_attivi} tavoli")

# ══════════════════════════════════════════════════════════════
# GENERAZIONE
# ══════════════════════════════════════════════════════════════

if btn_genera:
    ordini = raccolta_ordini()
    if not ordini:
        st.error("Nessun ospite configurato.")
    else:
        date_file = data_serata.strftime("%d%m%Y")
        pdfs = []
        progress = st.progress(0, text="Generazione PDF...")

        for idx, o in enumerate(ordini):
            fname = f"souvenir_{date_file}_{safe_filename(o['tavolo'])}_{safe_filename(o['nome'])}.pdf"
            out_path = OUTPUT_DIR / fname
            label = f"Tavolo {o['tavolo']} - {o['nome']}"

            try:
                pdf_bytes = genera_souvenir(
                    data_serata, o["tavolo"], o["nome"], o["lingua"],
                    o["tipo_menu"], o["piatti_csv"], output_path=out_path,
                    numero_ospite=o["numero_ospite"],
                )
                if pdf_bytes:
                    pdfs.append((label, fname, pdf_bytes))
                else:
                    st.error(f"{label}: generazione fallita (nessun output)")
            except Exception as e:
                st.error(f"{label}: {e}")

            progress.progress((idx + 1) / len(ordini), text=f"{label}...")

        progress.empty()
        st.session_state.pdfs = pdfs
        st.success(f"{len(pdfs)} PDF generati!")

# ══════════════════════════════════════════════════════════════
# ANTEPRIMA E DOWNLOAD
# ══════════════════════════════════════════════════════════════

if st.session_state.pdfs:
    pdfs = st.session_state.pdfs

    # ZIP in sidebar
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for _, fname, data in pdfs:
            zf.writestr(fname, data)
    with st.sidebar:
        st.download_button(
            "Scarica ZIP",
            data=zip_buf.getvalue(),
            file_name=f"souvenir_{data_serata.strftime('%d%m%Y')}.zip",
            mime="application/zip",
            use_container_width=True,
        )

    # Tabs anteprima
    st.subheader("Anteprima PDF")
    tabs = st.tabs([label for label, _, _ in pdfs])

    for tab, (label, fname, pdf_bytes) in zip(tabs, pdfs):
        with tab:
            # Download singolo
            st.download_button(
                f"Scarica {fname}",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                key=f"dl_{fname}",
            )
            # Render pagine con PyMuPDF a 150 DPI
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            cols = st.columns(min(len(doc), 2))
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                with cols[i % 2]:
                    st.image(img_bytes, caption=f"Pagina {i+1}", use_container_width=True)
            doc.close()
