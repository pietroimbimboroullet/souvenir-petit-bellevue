"""
genera_souvenir.py — Generatore souvenir menu Le Petit Bellevue
Legge ordini da file Excel (input/*.xlsx), genera un PDF per ogni ospite.
Font, spaziature e zone proibite dall'analisi pixel degli originali.
"""

import sys, io, json, re
from pathlib import Path
from datetime import datetime, date

from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit, ImageReader
from pypdf import PdfReader, PdfWriter
import fitz
from PIL import Image
import numpy as np
import openpyxl

# ══════════════════════════════════════════════════════════════
# PERCORSI
# ══════════════════════════════════════════════════════════════
ROOT       = Path(__file__).resolve().parent.parent
SFONDO     = ROOT / "Sfondo souvenir.pdf"
INPUT_DIR  = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
DB_FILE    = ROOT / "database" / "menu_database.json"
FONTS_DIR  = ROOT / "assets" / "fonts"

# ══════════════════════════════════════════════════════════════
# FONT
# ══════════════════════════════════════════════════════════════
pdfmetrics.registerFont(TTFont("Bellevue",        str(ROOT / "assets" / "Bellevue.ttf")))
pdfmetrics.registerFont(TTFont("BernhardMod",     str(FONTS_DIR / "Bernhard Modern BT.ttf")))
pdfmetrics.registerFont(TTFont("BernhardMod-It",  str(FONTS_DIR / "Bernhard Modern Italic BT.ttf")))
pdfmetrics.registerFont(TTFont("BernhardMod-Bd",  str(FONTS_DIR / "Bernhard Modern Bold BT.ttf")))
pdfmetrics.registerFont(TTFont("BernhardMod-BdIt",str(FONTS_DIR / "Bernhard Modern Bold Italic BT.ttf")))
print(f"Font caricati da: {FONTS_DIR}")
print("Font registrati OK")

# ══════════════════════════════════════════════════════════════
# DIMENSIONI PAGINA (A4 landscape)
# ══════════════════════════════════════════════════════════════
_bg_ref = PdfReader(str(SFONDO))
pw   = float(_bg_ref.pages[0].mediabox.width)   # 841.89 pt
ph   = float(_bg_ref.pages[0].mediabox.height)  # 595.28 pt
half = pw / 2                                     # 420.95 pt — asse di piega

# ══════════════════════════════════════════════════════════════
# ZONE PROIBITE — decorazioni pagina 2
# Ricavate da scansione pixel dello sfondo a 4x (feb 2026).
# Ogni zona: (x_left, x_right, rl_y_bottom, rl_y_top, descrizione).
# Il testo NON deve MAI entrare in queste aree + margine SAFETY.
# ══════════════════════════════════════════════════════════════
SAFETY = 5.7  # esattamente 2mm (1mm = 2.835pt)

# ── Profili decorazione per-Y — scansione pixel 4x (feb 2026) ──
# Tabelle lookup: per ogni coordinata Y (pt, indice 0..595),
# _LEFT_DECO_PROFILE[y]  = x_right max della decorazione sx (0 = nessuna)
# _RIGHT_DECO_PROFILE[y] = x_left min della decorazione dx (841 = nessuna)
# Ricavate da rendering 4x di "Sfondo souvenir.pdf" pagina 2,
# soglia distanza colore 25 dal bianco, arrotondate ceil/floor per sicurezza.
_LEFT_DECO_PROFILE = [
    46, 46, 46, 47, 47, 48, 49, 49, 50, 51,101,101,101, 99, 98, 96, 95, 94, 92, 91,
    90, 88, 87, 86, 84, 82, 81, 78, 75, 72, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45,
    46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46,
    46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 47, 47, 47, 48, 48, 49, 49,
    50, 50, 51, 51, 52, 52, 61, 63, 63, 65, 67, 67, 67, 66, 65, 67, 68, 68, 67, 67,
    64, 64, 64, 63, 58, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46,
    46, 47, 47, 47, 47, 47, 47, 47, 48, 48, 48, 49, 49, 49, 50, 51, 51, 52, 53, 54,
    54, 55, 56, 57, 59, 60, 62, 63, 65, 66, 68, 69, 71, 73, 74, 76, 77, 79, 81, 82,
    85, 86, 88, 89, 90, 91, 93, 94, 95, 98, 99, 99,100,101,102,102,102,102,102, 47,
    47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47,
    47, 47, 47, 47, 47, 47, 48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 49, 49, 49,
    50, 64, 67, 69, 70, 72, 73, 74, 75, 76, 77, 78, 79, 80, 82, 83, 84, 85, 86, 87,
    88, 89, 90, 91, 92, 92, 92, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49,
    49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 49, 50, 50,
    51, 51, 52, 86, 89, 90, 91, 92, 93, 94, 95, 96, 97, 97,144,148,150,152,153,154,
   155,157,158,159,159,160,161,162,162,163,163,163,129,130,130,130,131,132,134,134,
   134,135,135,133,132,100, 99, 98, 97, 96, 94, 93, 92, 91, 90, 88, 87, 86, 84, 82,
    80, 78, 76, 74, 71, 68, 47, 47, 47, 47, 47, 47, 47, 47, 47, 47, 46, 46, 46, 45,
    45, 45, 45, 46, 46, 47, 48, 49, 50, 51, 53, 54, 55, 57, 58, 59, 60, 61, 62, 63,
    64, 65, 66, 67, 68, 69, 70, 71, 71, 72, 73, 74, 74, 75, 76, 77, 78, 78, 79, 80,
    80, 80, 81, 82, 83, 83, 84, 84, 84, 85, 86, 86, 87, 87, 88, 88, 88, 89, 89, 90,
    90, 90, 91, 91, 92, 92, 92, 93, 93, 93, 93, 94, 94, 94, 95, 95, 96, 96, 96, 97,
    97, 97, 98, 98, 98, 99, 99, 99, 99,100,100,100,101,101,100,101,101,101,101,101,
   102,102,102,103,103,103,103,102,102,103,103,103,104,104,104,104,104,104,103,103,
   103,102,102,102,102,101,101,101,100,100, 99, 98, 97, 71, 71, 70, 71, 71, 72, 71,
    72, 73, 73, 73, 73, 73, 73, 74, 74, 74, 74, 75, 75, 75, 75, 75, 76, 76, 76, 76,
    76, 76, 76, 76, 77, 77, 77, 77, 77, 76,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
]

_RIGHT_DECO_PROFILE = [
   784,783,783,783,783,783,783,782,782,782,782,781,781,781,781,780,780,780,780,779,
   779,779,779,778,778,778,778,777,777,777,777,776,776,776,776,775,775,775,775,775,
   774,774,774,774,774,773,773,773,773,773,773,773,773,772,772,772,772,772,772,772,
   772,772,772,772,771,771,771,771,771,771,771,771,771,771,771,771,770,770,770,770,
   770,770,770,770,770,770,770,770,770,770,770,770,770,770,771,771,771,771,771,771,
   771,771,771,771,771,771,771,771,772,772,772,772,772,772,772,773,773,773,773,773,
   773,774,774,774,774,774,774,775,775,775,775,775,775,776,776,776,776,776,776,776,
   777,777,777,777,777,777,777,777,777,777,777,778,778,778,778,778,767,767,767,768,
   768,769,770,764,764,764,765,767,769,769,773,771,770,769,768,768,774,773,773,772,
   772,771,771,770,770,770,769,769,768,768,768,767,767,767,766,766,766,765,765,765,
   765,765,764,754,754,754,754,753,753,753,753,754,749,747,747,749,751,751,748,747,
   747,748,751,756,756,756,756,757,757,779,779,778,778,778,778,778,778,778,778,778,
   778,778,778,778,778,778,778,778,778,778,778,778,778,778,778,778,778,778,778,778,
   778,778,778,778,778,778,778,778,778,703,698,696,694,694,695,696,698,695,693,692,
   693,694,696,696,694,694,694,694,695,697,696,695,693,693,693,693,697,697,695,695,
   695,697,709,728,734,741,744,747,749,751,753,755,756,757,759,760,761,762,763,764,
   765,767,768,769,770,771,772,772,772,772,772,772,772,772,772,772,771,771,771,771,
   770,770,770,769,769,768,768,768,768,767,767,767,767,767,766,766,766,766,765,765,
   764,761,757,757,758,754,753,753,749,749,749,749,741,741,741,737,736,737,737,738,
   730,720,719,713,713,699,699,699,689,689,689,689,677,677,677,678,679,681,682,683,
   684,686,687,688,689,690,691,692,693,694,695,697,698,699,701,702,703,705,706,708,
   710,713,714,716,721,728,728,767,767,767,767,767,767,767,768,768,768,768,768,769,
   769,769,769,770,770,770,770,771,771,771,771,772,772,773,773,774,774,774,774,775,
   775,775,775,730,728,727,726,725,724,724,723,723,723,723,723,723,723,723,723,723,
   724,724,724,725,725,726,727,728,728,729,730,732,733,734,736,737,739,741,743,743,
   742,742,742,742,742,762,762,762,762,762,763,763,764,765,766,766,841,841,841,841,
   841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,
   841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,
   841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,
   841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,841,
]

def get_left_safe_margin(rl_y):
    """Ritorna il margine sinistro sicuro per una data coordinata Y.
    Scansiona ±SAFETY pt attorno a Y per catturare decorazioni vicine."""
    margin = 0
    yc = int(round(rl_y))
    buf = int(SAFETY) + 1
    for yi in range(max(0, yc - buf), min(len(_LEFT_DECO_PROFILE), yc + buf + 1)):
        deco = _LEFT_DECO_PROFILE[yi]
        if deco > 0:
            margin = max(margin, deco + SAFETY)
    return margin

def get_right_safe_margin(rl_y):
    """Ritorna il margine destro sicuro per una data coordinata Y.
    Scansiona ±SAFETY pt attorno a Y per catturare decorazioni vicine."""
    limit = pw
    yc = int(round(rl_y))
    buf = int(SAFETY) + 1
    for yi in range(max(0, yc - buf), min(len(_RIGHT_DECO_PROFILE), yc + buf + 1)):
        deco = _RIGHT_DECO_PROFILE[yi]
        if deco < 841:
            limit = min(limit, deco - SAFETY)
    return limit

def get_safe_margin_for_extent(y_baseline, font, size, side):
    """Margine sicuro considerando l'INTERA estensione verticale del testo.

    Controlla 3 punti Y (baseline, ascent, descent) e prende il margine
    più restrittivo — così nessun pixel del testo può entrare nelle zone.
    """
    face = pdfmetrics.getFont(font).face
    ascent = face.ascent / face.unitsPerEm * size
    descent = abs(face.descent) / face.unitsPerEm * size
    y_top = y_baseline + ascent
    y_bottom = y_baseline - descent
    if side == "left":
        return max(get_left_safe_margin(y_baseline),
                   get_left_safe_margin(y_top),
                   get_left_safe_margin(y_bottom))
    else:
        return min(get_right_safe_margin(y_baseline),
                   get_right_safe_margin(y_top),
                   get_right_safe_margin(y_bottom))

# ══════════════════════════════════════════════════════════════
# COSTANTI POSIZIONAMENTO — PAGINA 1 (copertina)
# ══════════════════════════════════════════════════════════════
P1_OVAL_BOTTOM_Y = 313.0
P1_ITALIC_TOP_Y  = 263.0
P1_DATE_X        = half + half / 2  # ~631 pt

# ══════════════════════════════════════════════════════════════
# COSTANTI POSIZIONAMENTO — PAGINA 2 (interno)
# ══════════════════════════════════════════════════════════════
P2_TITLE_Y        = ph - 55        # ~540 pt
P2_DISHES_START_Y = ph - 105       # ~490 pt
P2_DISHES_END_Y   = 25             # margine inferiore minimo
P2_LEFT_CENTER_X  = half / 2       # ~210 pt
P2_LEFT_MAX_X     = half - SAFETY  # ~415 pt — limite destro (piega - margine sicurezza)
P2_RIGHT_CENTER_X = half + half/2  # ~631 pt
P2_RIGHT_MIN_X    = half + SAFETY  # ~427 pt — limite sinistro metà destra (piega + margine)
P2_WINES_START_Y  = ph - ph / 3   # ~397 pt — 1/3 dall'alto
TITLE_MAX_W       = half - 30      # larghezza max titoli (metà pagina − 15pt margine/lato)

# ══════════════════════════════════════════════════════════════
# COLORI E DIMENSIONI
# ══════════════════════════════════════════════════════════════
CLR_DATE = (0.40, 0.26, 0.18)              # marrone/terra
DATE_FONT = "Bellevue"
DATE_SIZE = 14.5

CLR_MENU_TITLE     = (144/255, 154/255, 135/255)  # RGB(144,154,135) verde salvia
MENU_TITLE_OPACITY = 0.6
MENU_TITLE_SIZE    = 64

CLR_WINE_TITLE     = (56/255, 42/255, 102/255)    # RGB(56,42,102) viola scuro
WINE_TITLE_OPACITY = 0.6
WINE_TITLE_SIZE    = 48

# Piatti — font e dimensioni dall'analisi pixel di Souvenir Menu Esprit.pdf
CLR_DISH_NAME = (0.30, 0.22, 0.16)   # bruno scuro
CLR_DESC      = (0.42, 0.36, 0.30)   # bruno medio
SZ_DISH_NAME  = 20                    # Bernhard Modern Regular (dall'originale)
SZ_DESC       = 14                    # Bernhard Modern Italic (dall'originale)

# Separatore — immagine originale (Riga rossa.pdf) ricolorata
SEP_SRC     = ROOT / "Riga rossa.pdf"
SEP_DRAW_W  = 155                         # larghezza pt (dall'originale: ~37% metà pagina)
SEP_CLR     = (247, 195, 211)             # RGB target
SEP_OPACITY = 1.0                         # opacità massima (100%)

# Render PDF sorgente e ricolora
_doc = fitz.open(str(SEP_SRC))
_pix = _doc[0].get_pixmap(matrix=fitz.Matrix(4, 4))
_rgb = Image.frombytes("RGB", [_pix.width, _pix.height], _pix.samples)
_doc.close()

_arr = np.array(_rgb, dtype=np.float32)
# Maschera dalla distanza dal bianco (preserva antialiasing)
_mask = (255.0 - _arr.min(axis=2)) / 255.0
# Normalizza al valore massimo → nucleo della linea a 100% opacità
_mask_max = _mask.max()
if _mask_max > 0:
    _mask = _mask / _mask_max
_alpha = (_mask * SEP_OPACITY * 255).clip(0, 255).astype(np.uint8)

# Immagine RGBA con colore target e opacità
_result = np.zeros((_pix.height, _pix.width, 4), dtype=np.uint8)
_result[:, :, 0] = SEP_CLR[0]
_result[:, :, 1] = SEP_CLR[1]
_result[:, :, 2] = SEP_CLR[2]
_result[:, :, 3] = _alpha

_sep_pil = Image.fromarray(_result, "RGBA")
SEP_BUF = io.BytesIO()
_sep_pil.save(SEP_BUF, format="PNG")
SEP_BUF.seek(0)
SEP_READER = ImageReader(SEP_BUF)
SEP_ASPECT = _pix.width / _pix.height

# ══════════════════════════════════════════════════════════════
# METRICHE FONT — per spaziature precise
# ══════════════════════════════════════════════════════════════
name_face = pdfmetrics.getFont("BernhardMod").face
desc_face = pdfmetrics.getFont("BernhardMod-It").face

name_ascent  = name_face.ascent  / name_face.unitsPerEm * SZ_DISH_NAME
name_descent = abs(name_face.descent) / name_face.unitsPerEm * SZ_DISH_NAME
desc_ascent  = desc_face.ascent  / desc_face.unitsPerEm * SZ_DESC
desc_descent = abs(desc_face.descent) / desc_face.unitsPerEm * SZ_DESC

# Cap height (altezza maiuscole) per centraggio separatore
try:
    name_cap_h = name_face.capHeight / name_face.unitsPerEm * SZ_DISH_NAME
except AttributeError:
    name_cap_h = name_ascent
try:
    desc_cap_h = desc_face.capHeight / desc_face.unitsPerEm * SZ_DESC
except AttributeError:
    desc_cap_h = desc_ascent

# Interlinea (tra righe dello stesso elemento, es. nome che va a capo)
name_lh = SZ_DISH_NAME * 1.3   # 26 pt
desc_lh = SZ_DESC * 1.3         # 18.2 pt

# Distanza baseline-to-baseline da ultima riga nome a prima riga descrizione.
VISUAL_GAP_NAME_DESC = 12.5
NAME_DESC_BL = VISUAL_GAP_NAME_DESC + name_descent + desc_ascent

# Gap standard tra blocchi: riferimento da 7 piatti tipici (~54pt).
# Usato come tetto massimo per evitare gap enormi con pochi piatti.
_ref_avail = P2_DISHES_START_Y - P2_DISHES_END_Y
DISH_STD_GAP = (_ref_avail - 7 * NAME_DESC_BL) / 6

# Baseline data copertina (costante, indipendente dal contenuto)
date_face = pdfmetrics.getFont(DATE_FONT).face
date_cap_h = (date_face.ascent / date_face.unitsPerEm) * DATE_SIZE
_gap_mid = (P1_OVAL_BOTTOM_Y + P1_ITALIC_TOP_Y) / 2
DATE_BASELINE = _gap_mid - date_cap_h / 2

# ══════════════════════════════════════════════════════════════
# STAMPA DI VERIFICA
# ══════════════════════════════════════════════════════════════
print(f"\nMargine decorazioni: {SAFETY} pt ({SAFETY/2.835:.1f} mm)")
print(f"Font nomi: BernhardMod Regular {SZ_DISH_NAME}pt "
      f"(ascent={name_ascent:.1f}, descent={name_descent:.1f}, cap_h={name_cap_h:.1f})")
print(f"Font desc: BernhardMod-It {SZ_DESC}pt "
      f"(ascent={desc_ascent:.1f}, descent={desc_descent:.1f})")
print(f"Nome->desc baseline: {NAME_DESC_BL:.1f}pt "
      f"(= {VISUAL_GAP_NAME_DESC}pt gap + {name_descent:.1f}pt descent + {desc_ascent:.1f}pt ascent)")
print(f"Separatore: {SEP_SRC.name} ricolorato RGB{SEP_CLR} al {SEP_OPACITY*100:.0f}%, "
      f"larghezza={SEP_DRAW_W}pt")

# ══════════════════════════════════════════════════════════════
# DATABASE (lazy: può essere iniettato dall'esterno via set_db)
# ══════════════════════════════════════════════════════════════
DB = None

def _load_db_from_file():
    """Carica DB dal file JSON locale (fallback)."""
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def set_db(db_dict):
    """Inietta il database dall'esterno (es. da Supabase)."""
    global DB
    DB = db_dict

def get_db():
    """Ritorna il DB corrente; se non ancora caricato, carica da file."""
    global DB
    if DB is None:
        DB = _load_db_from_file()
    return DB

def find_dish(dish_id):
    """Cerca un piatto per ID (esatto -> prefisso -> contenuto).

    Normalizza spazi→underscore e minuscolo per tollerare sviste di battitura.
    """
    db = get_db()
    dish_id = dish_id.strip().lower().replace(" ", "_")
    for p in db["piatti"]:
        if p["id"] == dish_id:
            return p
    for p in db["piatti"]:
        if p["id"].startswith(dish_id):
            return p
    for p in db["piatti"]:
        if dish_id in p["id"]:
            return p
    return None

def get_dish_name_desc(dish, lang):
    """Ritorna (nome, descrizione) nella lingua dell'ospite.
    Legge direttamente nome_XX e ingredienti_XX dal database."""
    lang = lang if lang in ("it", "fr", "en") else "it"
    return dish.get(f"nome_{lang}", ""), dish.get(f"ingredienti_{lang}") or ""

# ══════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════
MENU_TITLES = {
    "esprit": "Esprit", "terroir": "Terroir",
    "carta": {"it": "Il percorso", "fr": "Le parcours", "en": "The journey"},
}
WINE_TITLES = {"it": "Dal regno di Bacco", "fr": "Du royaume de Bacchus",
               "en": "From Bacchus' world"}

GIORNI = {
    "it": {0: "Lunedì", 1: "Martedì", 2: "Mercoledì", 3: "Giovedì",
           4: "Venerdì", 5: "Sabato", 6: "Domenica"},
    "fr": {0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi",
           4: "Vendredi", 5: "Samedi", 6: "Dimanche"},
    "en": {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
           4: "Friday", 5: "Saturday", 6: "Sunday"},
}
MESI = {
    "it": {1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
           5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
           9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"},
    "fr": {1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
           5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
           9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"},
    "en": {1: "January", 2: "February", 3: "March", 4: "April",
           5: "May", 6: "June", 7: "July", 8: "August",
           9: "September", 10: "October", 11: "November", 12: "December"},
}

def format_date(dt, lingua="it"):
    """Formatta data nella lingua dell'ospite: 'Venerdì, 7 Febbraio 2026'."""
    lang = lingua if lingua in GIORNI else "it"
    return f"{GIORNI[lang][dt.weekday()]}, {dt.day} {MESI[lang][dt.month]} {dt.year}"

def parse_date(val):
    """Parse data da cella Excel (datetime, date o stringa DD/MM/YYYY)."""
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day)
    return datetime.strptime(str(val).strip(), "%d/%m/%Y")

def safe_filename(s):
    """Sanitizza stringa per uso come nome file."""
    return re.sub(r'[^\w\-.]', '_', str(s))

def balanced_split(text, font, size, max_width):
    """Spezza il testo in 2 righe bilanciate alla parola più vicina alla metà.
    Se entra in una riga, ritorna lista con una sola riga.
    Se una metà eccede max_width, fallback a simpleSplit."""
    tw = pdfmetrics.stringWidth(text, font, size)
    if tw <= max_width:
        return [text]
    words = text.split()
    if len(words) <= 1:
        return [text]
    target = tw / 2
    best_i, best_diff = 1, float('inf')
    for i in range(1, len(words)):
        w = pdfmetrics.stringWidth(' '.join(words[:i]), font, size)
        diff = abs(w - target)
        if diff < best_diff:
            best_diff = diff
            best_i = i
    line1 = ' '.join(words[:best_i])
    line2 = ' '.join(words[best_i:])
    w1 = pdfmetrics.stringWidth(line1, font, size)
    w2 = pdfmetrics.stringWidth(line2, font, size)
    if w1 <= max_width and w2 <= max_width:
        return [line1, line2]
    return simpleSplit(text, font, size, max_width)

def draw_line_safe(c, text, center_x, y, font, size, color, half_side="left"):
    """Disegna una riga centrata, spostata orizzontalmente se in zona proibita."""
    c.setFont(font, size)
    c.setFillColorRGB(*color)
    tw = pdfmetrics.stringWidth(text, font, size)
    x = center_x - tw / 2
    if half_side == "left":
        safe_left = get_left_safe_margin(y)
        if x < safe_left:
            x = safe_left
        # Clamp: il testo non deve mai superare la linea di piega
        if x + tw > P2_LEFT_MAX_X:
            x = P2_LEFT_MAX_X - tw
    elif half_side == "right":
        safe_right = get_right_safe_margin(y)
        if x + tw > safe_right:
            x = safe_right - tw
        # Clamp: il testo non deve mai superare la linea di piega a sinistra
        if x < P2_RIGHT_MIN_X:
            x = P2_RIGHT_MIN_X
    c.drawString(x, y, text)

# ══════════════════════════════════════════════════════════════
# FUNZIONI CONDIVISE — blocchi testo, posizionamento, separatori
# Piatti e vini usano le stesse funzioni con parametri diversi.
# ══════════════════════════════════════════════════════════════

def compute_block_h(n_name, n_desc):
    """Altezza di un blocco testo dal numero di righe nome/desc."""
    if n_desc > 0:
        return (n_name - 1) * name_lh + NAME_DESC_BL + (n_desc - 1) * desc_lh
    return (n_name - 1) * name_lh

def make_text_block(nome, desc, max_width):
    """Crea un blocco {nome, desc, name_lines, desc_lines, block_h, has_desc}."""
    nl = simpleSplit(nome, "BernhardMod", SZ_DISH_NAME, max_width)
    dl = balanced_split(desc, "BernhardMod-It", SZ_DESC, max_width) if desc else []
    return {
        "nome": nome, "desc": desc,
        "name_lines": nl, "desc_lines": dl,
        "block_h": compute_block_h(len(nl), len(dl)),
        "has_desc": len(dl) > 0,
    }

def _position_blocks_from_y(blocks, gap_h, top_y, end_y):
    """Posiziona blocchi partendo da top_y verso il basso."""
    N = len(blocks)
    if N == 0:
        return
    total_content = sum(b["block_h"] for b in blocks)
    gap_count = N - 1 if N > 1 else 1
    group_h = total_content + (gap_count * gap_h if N > 1 else 0)
    y = top_y
    if y - group_h < end_y:
        y = end_y + group_h
    for i, b in enumerate(blocks):
        b["y_start"] = y
        b["y_end"] = y - b["block_h"]
        if i < N - 1:
            y = b["y_end"] - gap_h


def position_blocks_vertically(blocks, gap_h, start_y, end_y, threshold, ref_y):
    """Posiziona blocchi verticalmente con logica di raggruppamento.
    N <= threshold: partenza da ref_y.
    N > threshold: gruppo centrato nell'area.
    Imposta y_start e y_end su ogni blocco."""
    N = len(blocks)
    if N == 0:
        return
    total_content = sum(b["block_h"] for b in blocks)
    gap_count = N - 1 if N > 1 else 1
    group_h = total_content + (gap_count * gap_h if N > 1 else 0)

    if N <= threshold:
        y = ref_y
        if y - group_h < end_y:
            y = end_y + group_h
    else:
        area_center = (start_y + end_y) / 2
        y = area_center + group_h / 2
        if y > start_y:
            y = start_y
        if y - group_h < end_y:
            y = end_y + group_h

    for i, b in enumerate(blocks):
        b["y_start"] = y
        b["y_end"] = y - b["block_h"]
        if i < N - 1:
            y = b["y_end"] - gap_h

def get_block_y_positions(block):
    """Restituisce tutte le coordinate Y delle righe di un blocco posizionato."""
    ys = []
    yc = block["y_start"]
    for j in range(len(block["name_lines"])):
        ys.append(yc)
        if j < len(block["name_lines"]) - 1:
            yc -= name_lh
    if block["has_desc"]:
        yc -= NAME_DESC_BL
        for j in range(len(block["desc_lines"])):
            ys.append(yc)
            if j < len(block["desc_lines"]) - 1:
                yc -= desc_lh
    return ys

def find_block_tightest_margin(block, safe_margin_fn, side):
    """Trova il margine sicuro più stretto per un blocco.

    Usa get_safe_margin_for_extent per controllare l'intera estensione
    verticale di ogni riga (baseline ± ascent/descent).
    side='left': ritorna max (margine sinistro più spinto a destra).
    side='right': ritorna min (margine destro più spinto a sinistra)."""
    margins = []
    yc = block["y_start"]
    for j in range(len(block["name_lines"])):
        margins.append(get_safe_margin_for_extent(
            yc, "BernhardMod", SZ_DISH_NAME, side))
        if j < len(block["name_lines"]) - 1:
            yc -= name_lh
    if block["has_desc"]:
        yc -= NAME_DESC_BL
        for j in range(len(block["desc_lines"])):
            margins.append(get_safe_margin_for_extent(
                yc, "BernhardMod-It", SZ_DESC, side))
            if j < len(block["desc_lines"]) - 1:
                yc -= desc_lh
    if side == "left":
        return max(margins) if margins else 0
    return min(margins) if margins else pw

def rewrap_block(block, safe_w, split_fn):
    """Re-splitta nome/desc per entrare in safe_w.
    Ritorna True se il numero di righe è cambiato."""
    new_nl = split_fn(block["nome"], "BernhardMod", SZ_DISH_NAME, safe_w)
    new_dl = balanced_split(block["desc"], "BernhardMod-It", SZ_DESC, safe_w) \
             if block["desc"] else []
    if len(new_nl) != len(block["name_lines"]) or \
       len(new_dl) != len(block["desc_lines"]):
        block["name_lines"] = new_nl
        block["desc_lines"] = new_dl
        block["has_desc"] = len(new_dl) > 0
        block["block_h"] = compute_block_h(len(new_nl), len(new_dl))
        return True
    return False

def collect_block_elements(blocks, center_x, side, label_prefix):
    """Crea elementi testo da blocchi posizionati.
    Ritorna lista di dict per elements[]. Ogni elemento ha block_idx
    per il riallineamento post-correzione."""
    elems = []
    for i, b in enumerate(blocks):
        y = b["y_start"]
        for j, line in enumerate(b["name_lines"]):
            tw = pdfmetrics.stringWidth(line, "BernhardMod", SZ_DISH_NAME)
            elems.append({
                "text": line, "x": center_x - tw / 2, "y": y,
                "font": "BernhardMod", "size": SZ_DISH_NAME,
                "color": CLR_DISH_NAME, "alpha": 1.0, "tw": tw,
                "side": side, "label": f"{label_prefix} {i+1} nome",
                "block_idx": i, "block_prefix": label_prefix,
            })
            if j < len(b["name_lines"]) - 1:
                y -= name_lh
        if b["has_desc"]:
            y -= NAME_DESC_BL
            for j, line in enumerate(b["desc_lines"]):
                tw = pdfmetrics.stringWidth(line, "BernhardMod-It", SZ_DESC)
                elems.append({
                    "text": line, "x": center_x - tw / 2, "y": y,
                    "font": "BernhardMod-It", "size": SZ_DESC,
                    "color": CLR_DESC, "alpha": 1.0, "tw": tw,
                    "side": side, "label": f"{label_prefix} {i+1} desc",
                    "block_idx": i, "block_prefix": label_prefix,
                })
                if j < len(b["desc_lines"]) - 1:
                    y -= desc_lh
    return elems

def place_block_separators(blocks, center_x, side="left"):
    """Crea separatori (righe rosse) tra blocchi consecutivi.
    Formula: punto medio visivo tra descent e cap_height."""
    seps = []
    for i in range(len(blocks) - 1):
        b = blocks[i]
        next_b = blocks[i + 1]
        if b["has_desc"]:
            y_vis_bottom = b["y_end"] - desc_descent
        else:
            y_vis_bottom = b["y_end"] - name_descent
        y_vis_top = next_b["y_start"] + name_cap_h
        sep_center_y = (y_vis_bottom + y_vis_top) / 2
        sep_draw_h = SEP_DRAW_W / SEP_ASPECT
        sep_x = center_x - SEP_DRAW_W / 2
        sep_y = sep_center_y - sep_draw_h / 2
        seps.append({"x": sep_x, "y": sep_y, "w": SEP_DRAW_W, "h": sep_draw_h,
                      "side": side})
    return seps

# ══════════════════════════════════════════════════════════════
# FUNZIONE PRINCIPALE: genera un PDF souvenir per un ospite
# ══════════════════════════════════════════════════════════════

def genera_souvenir(data_val, tavolo, ospite, lingua, tipo_menu,
                    piatti_csv, tipo_vini="", vini_raw="", output_path=None,
                    numero_ospite=None):
    """Genera un PDF souvenir per un singolo ospite."""

    dt = parse_date(data_val)
    lingua = str(lingua).strip().lower()
    date_text = format_date(dt, lingua)
    tipo_menu = str(tipo_menu).strip().lower()
    # Composizione menu degustazione: leggi piatti_ids dal DB
    db = get_db()
    menu_piatti_db = {}
    for m in db.get("menu_degustazione", []):
        if m.get("piatti_ids"):
            menu_piatti_db[m["id"]] = m["piatti_ids"]

    # Fallback hardcoded se il DB non ha piatti_ids
    MENU_PIATTI_FALLBACK = {
        "esprit": ["animelle", "spaghettoni_martelli", "piccione",
                    "carrello_formaggi", "nashi", "luna_rossa"],
        "terroir": ["sedano_rapa", "risotto_cavolo_viola", "zuppa_del_bosco",
                     "carrello_formaggi", "nashi", "topinambur"],
    }

    if tipo_menu in menu_piatti_db:
        piatti_ids = menu_piatti_db[tipo_menu]
    elif tipo_menu in MENU_PIATTI_FALLBACK:
        piatti_ids = MENU_PIATTI_FALLBACK[tipo_menu]
    else:
        # Carta: leggi dal campo piatti dell'Excel
        piatti_ids = [p.strip() for p in str(piatti_csv).split(",") if p.strip()]

    print(f"\n{'='*60}")
    print(f"Ospite: {ospite} | Tavolo: {tavolo} | Lingua: {lingua}")
    print(f"Menu: {tipo_menu}")

    # ── OVERLAY PAGINA 1 — data + numero tavolo/ospite ──
    buf1 = io.BytesIO()
    c1 = Canvas(buf1, pagesize=(pw, ph))
    c1.setFillColorRGB(*CLR_DATE)
    c1.setFont(DATE_FONT, DATE_SIZE)
    c1.drawCentredString(P1_DATE_X, DATE_BASELINE, date_text)

    # Numero tavolo e ospite — retro (metà sinistra), basso a sinistra, verticale
    if numero_ospite is not None:
        c1.saveState()
        c1.translate(15, 20)
        c1.rotate(270)
        c1.setFont("BernhardMod-It", 8)
        c1.setFillColorRGB(*CLR_DESC)
        c1.drawString(0, 0, f"{tavolo} - {numero_ospite}")
        c1.restoreState()

    c1.save()

    # ── OVERLAY PAGINA 2 — titoli + piatti + vini ──
    # Architettura: raccogli → verifica → disegna
    # Tutti gli elementi testuali vengono raccolti con le posizioni iniziali,
    # poi un controllo finale obbligatorio verifica e corregge eventuali
    # sovrapposizioni con le zone proibite, e infine disegna tutto.
    buf2 = io.BytesIO()
    c2 = Canvas(buf2, pagesize=(pw, ph))

    elements = []    # [{text, x, y, font, size, color, alpha, tw, side, label}]
    separators = []  # [{x, y, w, h}]

    # ── Titolo menu (metà SX) — verde salvia 60% ──
    title_raw = MENU_TITLES.get(tipo_menu, tipo_menu.capitalize())
    title_text = title_raw.get(lingua, title_raw.get("it", "")) if isinstance(title_raw, dict) else title_raw
    menu_sz = MENU_TITLE_SIZE
    title_tw = pdfmetrics.stringWidth(title_text, "Bellevue", menu_sz)
    if title_tw > TITLE_MAX_W:
        menu_sz = MENU_TITLE_SIZE * TITLE_MAX_W / title_tw
        title_tw = pdfmetrics.stringWidth(title_text, "Bellevue", menu_sz)
        print(f"  Titolo menu ridotto: {MENU_TITLE_SIZE}pt -> {menu_sz:.1f}pt "
              f"(tw={title_tw:.0f}pt <= {TITLE_MAX_W:.0f}pt)")
    elements.append({
        "text": title_text, "x": P2_LEFT_CENTER_X - title_tw / 2,
        "y": P2_TITLE_Y, "font": "Bellevue", "size": menu_sz,
        "color": CLR_MENU_TITLE, "alpha": MENU_TITLE_OPACITY,
        "tw": title_tw, "side": "left", "label": "titolo menu",
        "is_title": True,
    })

    # ── Titolo vini (metà DX) — viola scuro 60% ──
    wine_title = WINE_TITLES.get(lingua, WINE_TITLES["en"])
    wine_sz = WINE_TITLE_SIZE
    if "'" in wine_title:
        # Bellevue non ha il glifo apostrofo — segmenti con fallback BernhardMod
        parts = wine_title.split("'")
        def _build_wine_segs(sz):
            segs = []
            for i, part in enumerate(parts):
                if i > 0:
                    segs.append(("'", "BernhardMod", sz))
                if part:
                    segs.append((part, "Bellevue", sz))
            return segs
        seg_list = _build_wine_segs(wine_sz)
        total_w = sum(pdfmetrics.stringWidth(s, f, sz) for s, f, sz in seg_list)
        if total_w > TITLE_MAX_W:
            wine_sz = WINE_TITLE_SIZE * TITLE_MAX_W / total_w
            seg_list = _build_wine_segs(wine_sz)
            total_w = sum(pdfmetrics.stringWidth(s, f, sz) for s, f, sz in seg_list)
            print(f"  Titolo vini ridotto: {WINE_TITLE_SIZE}pt -> {wine_sz:.1f}pt "
                  f"(tw={total_w:.0f}pt <= {TITLE_MAX_W:.0f}pt)")
        x_seg = P2_RIGHT_CENTER_X - total_w / 2
        for seg_text, seg_font, seg_size in seg_list:
            seg_tw = pdfmetrics.stringWidth(seg_text, seg_font, seg_size)
            elements.append({
                "text": seg_text, "x": x_seg, "y": P2_TITLE_Y,
                "font": seg_font, "size": seg_size, "color": CLR_WINE_TITLE,
                "alpha": WINE_TITLE_OPACITY, "tw": seg_tw, "side": "right",
                "label": "titolo vini", "is_title": True,
            })
            x_seg += seg_tw
    else:
        wine_tw = pdfmetrics.stringWidth(wine_title, "Bellevue", wine_sz)
        if wine_tw > TITLE_MAX_W:
            wine_sz = WINE_TITLE_SIZE * TITLE_MAX_W / wine_tw
            wine_tw = pdfmetrics.stringWidth(wine_title, "Bellevue", wine_sz)
            print(f"  Titolo vini ridotto: {WINE_TITLE_SIZE}pt -> {wine_sz:.1f}pt "
                  f"(tw={wine_tw:.0f}pt <= {TITLE_MAX_W:.0f}pt)")
        elements.append({
            "text": wine_title, "x": P2_RIGHT_CENTER_X - wine_tw / 2,
            "y": P2_TITLE_Y, "font": "Bellevue", "size": wine_sz,
            "color": CLR_WINE_TITLE, "alpha": WINE_TITLE_OPACITY,
            "tw": wine_tw, "side": "right", "label": "titolo vini",
            "is_title": True,
        })

    # ── PIATTI — metà sinistra ──
    avail_width = half - 30

    dish_blocks = []
    for pid in piatti_ids:
        dish = find_dish(pid)
        if not dish:
            print(f"  [!] '{pid}' non trovato nel database")
            continue
        nome, desc = get_dish_name_desc(dish, lingua)
        dish_blocks.append(make_text_block(nome, desc, avail_width))

    N = len(dish_blocks)

    # Posizionamento piatti — logica adattiva
    total_available = P2_DISHES_START_Y - P2_DISHES_END_Y
    total_content = sum(b["block_h"] for b in dish_blocks)
    gap_count = N - 1 if N > 1 else 1

    if N >= 5:
        # Menu degustazione: distribuisci uniformemente su TUTTO lo spazio
        gap_height = (total_available - total_content) / gap_count
        position_blocks_vertically(dish_blocks, gap_height,
                                   P2_DISHES_START_Y, P2_DISHES_END_Y,
                                   0, P2_DISHES_START_Y)
    else:
        # Pochi piatti (carta): posiziona a 1/3 dall'alto
        gap_height = min(DISH_STD_GAP, (total_available - total_content) / gap_count)
        group_h = total_content + (gap_count * gap_height if N > 1 else 0)
        y_top = P2_DISHES_START_Y - (total_available - group_h) / 3
        _position_blocks_from_y(dish_blocks, gap_height, y_top, P2_DISHES_END_Y)

    # Re-wrap iterativo: ri-splitta SOLO se il testo non entra nello
    # spazio fisico tra decorazione e piega (fit_w). Non re-wrappare
    # per centratura: il RIALLINEAMENTO BLOCCHI gestisce lo spostamento.
    for _iter in range(3):
        rewrapped = False
        for b in dish_blocks:
            margin = find_block_tightest_margin(b, get_left_safe_margin, "left")
            fit_w = P2_LEFT_MAX_X - margin
            if fit_w <= 0:
                continue
            too_wide = any(
                pdfmetrics.stringWidth(l, "BernhardMod", SZ_DISH_NAME) > fit_w
                for l in b["name_lines"]
            ) or any(
                pdfmetrics.stringWidth(l, "BernhardMod-It", SZ_DESC) > fit_w
                for l in b["desc_lines"]
            )
            if too_wide and rewrap_block(b, fit_w, simpleSplit):
                rewrapped = True
        if not rewrapped:
            break
        # Riposiziona dopo re-wrap
        total_content = sum(b["block_h"] for b in dish_blocks)
        if N >= 5:
            gap_height = (total_available - total_content) / gap_count
            position_blocks_vertically(dish_blocks, gap_height,
                                       P2_DISHES_START_Y, P2_DISHES_END_Y,
                                       0, P2_DISHES_START_Y)
        else:
            gap_height = min(DISH_STD_GAP, (total_available - total_content) / gap_count)
            group_h = total_content + (gap_count * gap_height if N > 1 else 0)
            y_top = P2_DISHES_START_Y - (total_available - group_h) / 3
            _position_blocks_from_y(dish_blocks, gap_height, y_top, P2_DISHES_END_Y)

    dish_mode = "distribuito" if N >= 5 else "1/3 dall'alto"
    print(f"  Piatti: {N} blocchi ({dish_mode}), gap={gap_height:.1f}pt")

    # Raccogli elementi piatti + separatori
    elements.extend(collect_block_elements(
        dish_blocks, P2_LEFT_CENTER_X, "left", "piatto"))
    separators.extend(place_block_separators(
        dish_blocks, P2_LEFT_CENTER_X, "left"))

    # ── RIGHE PER SCRITTURA — metà destra ──
    # Linee rosse orizzontali spaziate 8mm per scrittura a mano
    RULED_LINE_SPACING = 22.68  # 8mm in punti (8 * 2.835)
    ruled_y_start = P2_DISHES_START_Y + RULED_LINE_SPACING       # +1 riga in alto
    ruled_y_end = (P2_DISHES_END_Y + 0.25 * (P2_DISHES_START_Y - P2_DISHES_END_Y)
                   - 2 * RULED_LINE_SPACING)                     # +2 righe in basso

    ruled_lines = []
    y = ruled_y_start
    while y >= ruled_y_end:
        # Rispetta decorazioni destra
        yi = int(max(0, min(len(_RIGHT_DECO_PROFILE) - 1, y)))
        safe_right = _RIGHT_DECO_PROFILE[yi]
        if safe_right < 841:
            safe_right -= SAFETY
        else:
            safe_right = pw - 15
        x1 = half + 15
        x2 = safe_right
        if x2 - x1 > 30:
            ruled_lines.append({"x1": x1, "x2": x2, "y": y})
        y -= RULED_LINE_SPACING

    print(f"  Righe scrittura: {len(ruled_lines)} linee (8mm, "
          f"y={ruled_y_start:.0f}..{ruled_y_end:.0f})")

    # ── Firme Chef e Sommelier — metà destra, sotto le righe ──
    chef_name = "Niccolò de Riu"
    somm_name = "Rino Billia"
    chef_titles = {"it": "Lo Chef", "fr": "Le Chef", "en": "The Chef"}
    somm_titles = {"it": "Il Sommelier", "fr": "Le Sommelier", "en": "The Sommelier"}
    chef_title = chef_titles.get(lingua, chef_titles["it"])
    somm_title = somm_titles.get(lingua, somm_titles["it"])

    sig_name_y = P2_DISHES_END_Y + 40
    sig_title_y = sig_name_y - desc_lh
    sig_chef_cx = half + half * 0.25
    sig_somm_cx = half + half * 0.58

    for text, cx, label in [
        (chef_name, sig_chef_cx, "firma chef nome"),
        (somm_name, sig_somm_cx, "firma somm nome"),
    ]:
        tw = pdfmetrics.stringWidth(text, "BernhardMod-It", SZ_DESC)
        elements.append({
            "text": text, "x": cx - tw / 2, "y": sig_name_y,
            "font": "BernhardMod-It", "size": SZ_DESC,
            "color": CLR_DESC, "alpha": 1.0, "tw": tw,
            "side": "right", "label": label, "no_recenter": True,
        })
    for text, cx, label in [
        (chef_title, sig_chef_cx, "firma chef titolo"),
        (somm_title, sig_somm_cx, "firma somm titolo"),
    ]:
        tw = pdfmetrics.stringWidth(text, "BernhardMod-It", SZ_DESC)
        elements.append({
            "text": text, "x": cx - tw / 2, "y": sig_title_y,
            "font": "BernhardMod-It", "size": SZ_DESC,
            "color": CLR_DESC, "alpha": 1.0, "tw": tw,
            "side": "right", "label": label, "no_recenter": True,
        })

    # ══════════════════════════════════════════════════════════════
    # CONTROLLO FINALE ASSOLUTO
    # Verifica OGNI elemento con l'intera estensione verticale del testo
    # (baseline ± ascent/descent). Se dopo la correzione il testo è ancora
    # dentro una zona proibita → ABORT: il PDF NON viene generato.
    # ══════════════════════════════════════════════════════════════
    print(f"  Controllo finale ASSOLUTO ({len(elements)} elementi):")
    fixes = 0
    errors = []
    for el in elements:
        old_x = el["x"]
        tw = el["tw"]
        y_el = el["y"]
        is_title = el.get("is_title", False)

        if is_title:
            pass  # Titoli decorativi: posizione centrata, nessun vincolo

        elif el["side"] == "left":
            # Margine sicuro con estensione verticale COMPLETA
            safe_left = get_safe_margin_for_extent(
                y_el, el["font"], el["size"], "left")
            # 1) Non sovrapporre decorazioni a sinistra
            if el["x"] < safe_left:
                el["x"] = safe_left
            # 2) Non superare la piega a destra
            if el["x"] + tw > P2_LEFT_MAX_X:
                el["x"] = P2_LEFT_MAX_X - tw
            # VERIFICA POST-FIX: ancora in zona?
            if el["x"] < safe_left or el["x"] + tw > P2_LEFT_MAX_X:
                errors.append(el)

        elif el["side"] == "right":
            # Margine sicuro con estensione verticale COMPLETA
            safe_right = get_safe_margin_for_extent(
                y_el, el["font"], el["size"], "right")
            # 1) Non sovrapporre decorazioni a destra
            if el["x"] + tw > safe_right:
                el["x"] = safe_right - tw
            # 2) Non superare la piega a sinistra
            if el["x"] < P2_RIGHT_MIN_X:
                el["x"] = P2_RIGHT_MIN_X
            # VERIFICA POST-FIX: ancora in zona?
            if el["x"] + tw > safe_right or el["x"] < P2_RIGHT_MIN_X:
                errors.append(el)

        if abs(el["x"] - old_x) > 0.5:
            fixes += 1
            print(f"    [FIX] {el['label']}: y={y_el:.0f} "
                  f"x {old_x:.0f}->{el['x']:.0f} "
                  f"[{el['x']:.0f}..{el['x']+tw:.0f}]")
        else:
            print(f"    [OK]  {el['label']}: y={y_el:.0f} "
                  f"[{el['x']:.0f}..{el['x']+tw:.0f}]")

    if errors:
        print(f"\n  [ERRORE CRITICO] {len(errors)} elementi impossibili da posizionare:")
        for el in errors:
            print(f"    ABORT: {el['label']} a y={el['y']:.0f} "
                  f"[{el['x']:.0f}..{el['x']+el['tw']:.0f}]")
        print(f"  >>> PDF NON generato per {ospite}")
        return
    elif fixes:
        print(f"  >>> {fixes} elementi corretti")
    else:
        print(f"  >>> Nessuna sovrapposizione")

    # ── CENTRATURA RIGHE INDIPENDENTI ──
    # Ogni riga viene centrata sull'asse della colonna indipendentemente.
    # Se la decorazione impedisce la centratura perfetta, la riga viene
    # spostata solo quanto basta. Non c'è un centro comune per blocco.
    # (Il CONTROLLO FINALE sopra ha già spostato le righe che sforano,
    #  qui ricentro quelle che possono stare più vicine all'asse.)
    recenter_fixes = 0
    for el in elements:
        if el.get("is_title") or el.get("no_recenter"):
            continue
        tw = el["tw"]
        side = el["side"]
        if side == "left":
            ideal_x = P2_LEFT_CENTER_X - tw / 2
            safe_left = get_safe_margin_for_extent(
                el["y"], el["font"], el["size"], "left")
            new_x = max(ideal_x, safe_left)
            if new_x + tw > P2_LEFT_MAX_X:
                new_x = P2_LEFT_MAX_X - tw
        else:
            ideal_x = P2_RIGHT_CENTER_X - tw / 2
            safe_right = get_safe_margin_for_extent(
                el["y"], el["font"], el["size"], "right")
            new_x = min(ideal_x, safe_right - tw)
            if new_x < P2_RIGHT_MIN_X:
                new_x = P2_RIGHT_MIN_X
        if abs(new_x - el["x"]) > 0.5:
            recenter_fixes += 1
            el["x"] = new_x

    if recenter_fixes:
        print(f"  Centratura righe: {recenter_fixes} righe ricentrate")

    # ── CONTROLLO SEPARATORI CONTRO DECORAZIONI ──
    # I separatori (righe rosse) vengono verificati e ridotti se necessario.
    print(f"  Controllo separatori ({len(separators)}):")
    sep_fixes = 0
    valid_separators = []
    for si, sep in enumerate(separators):
        old_x = sep["x"]
        old_w = sep["w"]
        side = sep.get("side", "left")
        sep_y_lo = int(max(0, sep["y"] - 1))
        sep_y_hi = int(min(len(_LEFT_DECO_PROFILE) - 1, sep["y"] + sep["h"] + 1))

        if side == "left":
            # Margine sinistro più restrittivo nell'area del separatore
            safe_left = 0
            for yi in range(sep_y_lo, sep_y_hi + 1):
                deco = _LEFT_DECO_PROFILE[yi]
                if deco > 0:
                    safe_left = max(safe_left, deco + SAFETY)
            new_x = max(sep["x"], safe_left)
            new_right = min(sep["x"] + sep["w"], P2_LEFT_MAX_X)
        else:
            # Margine destro più restrittivo nell'area del separatore
            safe_right = pw
            for yi in range(sep_y_lo, sep_y_hi + 1):
                if yi < len(_RIGHT_DECO_PROFILE):
                    deco = _RIGHT_DECO_PROFILE[yi]
                    if deco < 841:
                        safe_right = min(safe_right, deco - SAFETY)
            new_x = max(sep["x"], P2_RIGHT_MIN_X)
            new_right = min(sep["x"] + sep["w"], safe_right)

        new_w = new_right - new_x
        if new_w < 30:
            print(f"    [SKIP] sep {si+1}: y={sep['y']:.0f} troppo stretto ({new_w:.0f}pt)")
            continue

        if abs(new_x - old_x) > 0.5 or abs(new_w - old_w) > 0.5:
            sep_fixes += 1
            sep["x"] = new_x
            sep["w"] = new_w
            sep["h"] = new_w / SEP_ASPECT
            print(f"    [FIX] sep {si+1}: y={sep['y']:.0f} "
                  f"x {old_x:.0f}->{new_x:.0f} w {old_w:.0f}->{new_w:.0f}")
        else:
            print(f"    [OK]  sep {si+1}: y={sep['y']:.0f} "
                  f"[{sep['x']:.0f}..{sep['x']+sep['w']:.0f}]")
        valid_separators.append(sep)

    separators = valid_separators
    if sep_fixes:
        print(f"  >>> {sep_fixes} separatori corretti")

    # ══════════════════════════════════════════════════════════════
    # DISEGNO — tutte le posizioni sono state verificate
    # ══════════════════════════════════════════════════════════════
    for el in elements:
        if el["alpha"] < 1.0:
            c2.saveState()
            c2.setFillAlpha(el["alpha"])
        c2.setFont(el["font"], el["size"])
        c2.setFillColorRGB(*el["color"])
        c2.drawString(el["x"], el["y"], el["text"])
        if el["alpha"] < 1.0:
            c2.restoreState()

    for sep in separators:
        c2.drawImage(SEP_READER, sep["x"], sep["y"],
                     width=sep["w"], height=sep["h"], mask="auto")

    # Righe per scrittura a mano
    c2.setStrokeColorRGB(247/255, 195/255, 211/255)
    c2.setLineWidth(0.75)
    for rl in ruled_lines:
        c2.line(rl["x1"], rl["y"], rl["x2"], rl["y"])

    c2.save()

    # ── ASSEMBLAGGIO ──
    bg = PdfReader(str(SFONDO))
    writer = PdfWriter()

    p1 = bg.pages[0]
    p1.merge_page(PdfReader(buf1).pages[0])
    writer.add_page(p1)

    p2 = bg.pages[1]
    p2.merge_page(PdfReader(buf2).pages[0])
    writer.add_page(p2)

    pdf_buf = io.BytesIO()
    writer.write(pdf_buf)
    pdf_bytes = pdf_buf.getvalue()

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"  -> {output_path.name}")

    return pdf_bytes

# ══════════════════════════════════════════════════════════════
# MAIN: lettura Excel e generazione PDF
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    xlsx_files = sorted(INPUT_DIR.glob("*.xlsx"))
    if not xlsx_files:
        print("\n[ERRORE] Nessun file .xlsx trovato in input/")
        sys.exit(1)

    xlsx_path = xlsx_files[0]
    print(f"\nLettura ordini: {xlsx_path.name}")

    wb_xl = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb_xl["ORDINI"]

    count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        data_val, tavolo, ospite, lingua, tipo_menu, piatti, tipo_vini, vini = row

        # Nome file: souvenir_DDMMYYYY_tavolo_ospite.pdf
        dt = parse_date(data_val)
        date_file = dt.strftime("%d%m%Y")
        fname = f"souvenir_{date_file}_{safe_filename(tavolo)}_{safe_filename(ospite)}.pdf"
        out_path = OUTPUT_DIR / fname

        genera_souvenir(data_val, tavolo, ospite, lingua, tipo_menu,
                        piatti, tipo_vini, vini, out_path)
        count += 1

    wb_xl.close()
    print(f"\n{'='*60}")
    print(f"Completato: {count} PDF generati in {OUTPUT_DIR}")
