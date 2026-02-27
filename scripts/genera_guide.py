"""
genera_guide.py — Genera due PDF guida per il progetto Souvenir Petit Bellevue:
  1. Guida tecnica (installazione su nuovo PC)
  2. Guida utente (per il ricevimento)
Stile: nerd ma con colori pastello eleganti.
"""

import sys
from pathlib import Path
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Percorsi ──
ROOT = Path(r"C:\Users\Pietro\Desktop\Claude\Souvenir Petit Bellevue")
FONTS_DIR = Path(r"C:\Users\Pietro\AppData\Local\Microsoft\Windows\Fonts")
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Font ──
pdfmetrics.registerFont(TTFont("Bellevue", str(ROOT / "assets" / "Bellevue.ttf")))
pdfmetrics.registerFont(TTFont("BernhardMod", str(FONTS_DIR / "Bernhard Modern BT.ttf")))
pdfmetrics.registerFont(TTFont("BernhardMod-It", str(FONTS_DIR / "Bernhard Modern Italic BT.ttf")))
pdfmetrics.registerFont(TTFont("BernhardMod-Bd", str(FONTS_DIR / "Bernhard Modern Bold BT.ttf")))
pdfmetrics.registerFont(TTFont("BernhardMod-BdIt", str(FONTS_DIR / "Bernhard Modern Bold Italic BT.ttf")))

# ══════════════════════════════════════════════════════════════
# PALETTE PASTELLO
# ══════════════════════════════════════════════════════════════
CLR_BG         = HexColor("#FAF6EF")  # panna / ivory chiaro (sfondo pagina)
CLR_TITLE      = HexColor("#5B3A6B")  # viola scuro elegante
CLR_SUBTITLE   = HexColor("#7B5E8D")  # viola medio
CLR_BODY       = HexColor("#3E3E3E")  # grigio scuro corpo
CLR_CODE_BG    = HexColor("#F0E8F5")  # lavanda chiarissimo (sfondo codice)
CLR_CODE_FG    = HexColor("#4A2D6B")  # viola scuro (testo codice)
CLR_ACCENT     = HexColor("#D4A0B9")  # rosa pastello (linee, accenti)
CLR_WARN_BG    = HexColor("#FFF3E0")  # arancio chiaro (avvisi)
CLR_WARN_FG    = HexColor("#8D5524")  # marrone (testo avvisi)
CLR_TIP_BG     = HexColor("#E8F5E9")  # verde chiaro (suggerimenti)
CLR_TIP_FG     = HexColor("#2E5B3A")  # verde scuro
CLR_STEP_NUM   = HexColor("#B07DC9")  # viola pastello (numero step)
CLR_HEADER_LINE = HexColor("#D4A0B9") # rosa pastello (linea sotto header)

# ══════════════════════════════════════════════════════════════
# STILI
# ══════════════════════════════════════════════════════════════

style_title = ParagraphStyle(
    "GuideTitle", fontName="Bellevue", fontSize=32, leading=40,
    textColor=CLR_TITLE, alignment=TA_CENTER, spaceAfter=4*mm,
)
style_subtitle = ParagraphStyle(
    "GuideSubtitle", fontName="BernhardMod-It", fontSize=13, leading=17,
    textColor=CLR_SUBTITLE, alignment=TA_CENTER, spaceAfter=10*mm,
)
style_h1 = ParagraphStyle(
    "H1", fontName="BernhardMod-Bd", fontSize=16, leading=20,
    textColor=CLR_TITLE, spaceBefore=8*mm, spaceAfter=3*mm,
)
style_h2 = ParagraphStyle(
    "H2", fontName="BernhardMod-Bd", fontSize=12, leading=15,
    textColor=CLR_SUBTITLE, spaceBefore=5*mm, spaceAfter=2*mm,
)
style_body = ParagraphStyle(
    "Body", fontName="BernhardMod", fontSize=10, leading=14,
    textColor=CLR_BODY, spaceAfter=2*mm,
)
style_body_bold = ParagraphStyle(
    "BodyBold", fontName="BernhardMod-Bd", fontSize=10, leading=14,
    textColor=CLR_BODY, spaceAfter=2*mm,
)
style_code = ParagraphStyle(
    "Code", fontName="Courier", fontSize=9, leading=13,
    textColor=CLR_CODE_FG, backColor=CLR_CODE_BG,
    borderPadding=(4, 6, 4, 6), spaceAfter=3*mm,
    leftIndent=8*mm,
)
style_bullet = ParagraphStyle(
    "Bullet", fontName="BernhardMod", fontSize=10, leading=14,
    textColor=CLR_BODY, leftIndent=10*mm, bulletIndent=4*mm,
    spaceAfter=1.5*mm,
)
style_step = ParagraphStyle(
    "Step", fontName="BernhardMod", fontSize=11, leading=15,
    textColor=CLR_BODY, leftIndent=12*mm, spaceAfter=2*mm,
)
style_step_big = ParagraphStyle(
    "StepBig", fontName="BernhardMod", fontSize=14, leading=19,
    textColor=CLR_BODY, leftIndent=14*mm, spaceAfter=3*mm,
)
style_footer = ParagraphStyle(
    "Footer", fontName="BernhardMod-It", fontSize=8, leading=10,
    textColor=CLR_ACCENT, alignment=TA_CENTER,
)
style_warning = ParagraphStyle(
    "Warning", fontName="BernhardMod-It", fontSize=9.5, leading=13,
    textColor=CLR_WARN_FG, backColor=CLR_WARN_BG,
    borderPadding=(4, 6, 4, 6), spaceAfter=3*mm, leftIndent=4*mm,
)
style_tip = ParagraphStyle(
    "Tip", fontName="BernhardMod-It", fontSize=9.5, leading=13,
    textColor=CLR_TIP_FG, backColor=CLR_TIP_BG,
    borderPadding=(4, 6, 4, 6), spaceAfter=3*mm, leftIndent=4*mm,
)

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def accent_line():
    return HRFlowable(
        width="80%", thickness=0.75, color=CLR_HEADER_LINE,
        spaceBefore=1*mm, spaceAfter=3*mm, hAlign="CENTER",
    )

def step(n, text, big=False):
    s = style_step_big if big else style_step
    return Paragraph(
        f'<font name="BernhardMod-Bd" color="{CLR_STEP_NUM.hexval()}">{n}.</font>  {text}', s
    )

def bullet(text):
    return Paragraph(f'<bullet>&bull;</bullet> {text}', style_bullet)

def code(text):
    return Paragraph(text.replace("\n", "<br/>"), style_code)

def warn(text):
    return Paragraph(f'<font name="BernhardMod-Bd">Attenzione:</font> {text}', style_warning)

def tip(text):
    return Paragraph(f'<font name="BernhardMod-Bd">Suggerimento:</font> {text}', style_tip)

def page_bg(canvas, doc):
    """Sfondo crema su ogni pagina + footer."""
    canvas.saveState()
    canvas.setFillColor(CLR_BG)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    # footer
    canvas.setFont("BernhardMod-It", 7)
    canvas.setFillColor(CLR_ACCENT)
    canvas.drawCentredString(A4[0] / 2, 12*mm,
        f"Souvenir Petit Bellevue  —  {date.today().strftime('%d/%m/%Y')}")
    canvas.restoreState()


# ══════════════════════════════════════════════════════════════
# 1. GUIDA TECNICA
# ══════════════════════════════════════════════════════════════

def genera_guida_tecnica():
    path = OUTPUT_DIR / "Guida_Tecnica_Souvenir.pdf"
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        topMargin=20*mm, bottomMargin=20*mm,
        leftMargin=18*mm, rightMargin=18*mm,
    )

    story = []

    # ── Copertina ──
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("Souvenir Petit Bellevue", style_title))
    story.append(accent_line())
    story.append(Paragraph("Guida tecnica di installazione", style_subtitle))
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        "Tutto il necessario per installare e configurare il generatore di souvenir "
        "su una nuova postazione Windows.",
        ParagraphStyle("Intro", parent=style_body, fontSize=11, leading=15,
                       alignment=TA_CENTER, textColor=CLR_SUBTITLE)
    ))
    story.append(Spacer(1, 15*mm))

    # Tabella riepilogo requisiti
    req_data = [
        ["Requisito", "Dettaglio"],
        ["Sistema operativo", "Windows 10 / 11"],
        ["Python", "3.10 o superiore"],
        ["Font di sistema", "Bernhard Modern BT (4 file)"],
        ["Spazio disco", "~50 MB"],
        ["Connessione internet", "Solo per installazione pacchetti"],
    ]
    req_table = Table(req_data, colWidths=[45*mm, 100*mm])
    req_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "BernhardMod-Bd"),
        ("FONTNAME", (0, 1), (-1, -1), "BernhardMod"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, 0), CLR_TITLE),
        ("TEXTCOLOR", (0, 1), (-1, -1), CLR_BODY),
        ("BACKGROUND", (0, 0), (-1, 0), CLR_CODE_BG),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, CLR_ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(req_table)
    story.append(PageBreak())

    # ── 1. Installare Python ──
    story.append(Paragraph("1. Installare Python", style_h1))
    story.append(accent_line())
    story.append(step(1, "Vai su <b>python.org/downloads</b> e scarica Python 3.10+"))
    story.append(step(2, 'All\'avvio dell\'installer, spunta <b>"Add Python to PATH"</b> (fondamentale!)'))
    story.append(step(3, 'Clicca <b>"Install Now"</b> e attendi il completamento'))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("Verifica installazione — apri il Prompt dei comandi (cmd) e digita:", style_body))
    story.append(code("python --version"))
    story.append(Paragraph("Deve mostrare <b>Python 3.10.x</b> o superiore.", style_body))
    story.append(warn(
        'Se il comando non viene riconosciuto, Python non e\' nel PATH. '
        'Reinstalla spuntando "Add Python to PATH" oppure aggiungilo manualmente '
        'dalle Impostazioni di Sistema &gt; Variabili d\'ambiente.'
    ))

    # ── 2. Font Bernhard Modern ──
    story.append(Paragraph("2. Installare i font Bernhard Modern BT", style_h1))
    story.append(accent_line())
    story.append(Paragraph(
        "Il programma usa la famiglia <b>Bernhard Modern BT</b> (4 varianti). "
        "Questi font devono essere installati nel sistema.",
        style_body
    ))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("I 4 file necessari:", style_body_bold))
    story.append(bullet("Bernhard Modern BT.ttf  <i>(regular)</i>"))
    story.append(bullet("Bernhard Modern Italic BT.ttf  <i>(corsivo)</i>"))
    story.append(bullet("Bernhard Modern Bold BT.ttf  <i>(grassetto)</i>"))
    story.append(bullet("Bernhard Modern Bold Italic BT.ttf  <i>(grassetto corsivo)</i>"))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("<b>Dove trovarli:</b>", style_body))
    story.append(Paragraph(
        "Sulla postazione attuale si trovano in:",
        style_body
    ))
    story.append(code(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts"))
    story.append(Paragraph(
        "Copia i 4 file .ttf su una chiavetta USB.",
        style_body
    ))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("<b>Come installarli sulla nuova postazione:</b>", style_body))
    story.append(step(1, "Copia i 4 file .ttf sul desktop del nuovo PC"))
    story.append(step(2, "Seleziona tutti e 4 i file"))
    story.append(step(3, "Clic destro &gt; <b>Installa per tutti gli utenti</b>"))
    story.append(tip(
        'Se "Installa per tutti gli utenti" non appare, fai doppio clic su ciascun file '
        'e premi il pulsante "Installa" nella finestra di anteprima.'
    ))
    story.append(warn(
        "Dopo l'installazione, verifica il percorso dove Windows li ha messi. "
        "Se sono in una cartella diversa da quella indicata nello script, "
        "dovrai aggiornare il percorso (vedi sezione 4)."
    ))

    # ── 3. Copiare il progetto ──
    story.append(Paragraph("3. Copiare la cartella del progetto", style_h1))
    story.append(accent_line())
    story.append(step(1, 'Copia l\'intera cartella <b>"Souvenir Petit Bellevue"</b> su chiavetta USB'))
    story.append(step(2, "Incollala sul Desktop del nuovo PC (o nella posizione desiderata)"))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("La struttura deve contenere almeno:", style_body))
    story.append(code(
        "Souvenir Petit Bellevue/<br/>"
        "  assets/Bellevue.ttf<br/>"
        "  database/menu_database.json<br/>"
        "  scripts/genera_souvenir.py<br/>"
        "  app.py<br/>"
        "  Sfondo souvenir.pdf<br/>"
        "  Riga rossa.pdf<br/>"
        "  requirements.txt<br/>"
        "  Avvia Souvenir.bat"
    ))

    # ── 4. Aggiornare i percorsi ──
    story.append(Paragraph("4. Aggiornare i percorsi nello script", style_h1))
    story.append(accent_line())
    story.append(Paragraph(
        "Lo script <b>genera_souvenir.py</b> contiene due percorsi assoluti da aggiornare "
        "se la posizione sul nuovo PC e' diversa.",
        style_body
    ))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("Apri il file <b>scripts/genera_souvenir.py</b> con un editor di testo e modifica:", style_body))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("<b>Riga 24</b> — Percorso della cartella del progetto:", style_body_bold))
    story.append(code(
        '# DA:<br/>'
        'ROOT = Path(r"C:\\Users\\Pietro\\Desktop\\Claude\\Souvenir Petit Bellevue")<br/>'
        '<br/>'
        '# A (esempio):<br/>'
        'ROOT = Path(r"C:\\Users\\NUOVO_UTENTE\\Desktop\\Souvenir Petit Bellevue")'
    ))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("<b>Riga 29</b> — Percorso dei font Bernhard:", style_body_bold))
    story.append(code(
        '# DA:<br/>'
        'FONTS_DIR = Path(r"C:\\Users\\Pietro\\AppData\\Local\\Microsoft\\Windows\\Fonts")<br/>'
        '<br/>'
        '# A (esempio, se installati "per tutti gli utenti"):<br/>'
        'FONTS_DIR = Path(r"C:\\Windows\\Fonts")'
    ))
    story.append(warn(
        "Il percorso dei font dipende da come sono stati installati. "
        'Se installati con "Installa per tutti gli utenti", si trovano in <b>C:\\Windows\\Fonts</b>. '
        "Se installati solo per l'utente corrente, si trovano in "
        "<b>%LOCALAPPDATA%\\Microsoft\\Windows\\Fonts</b> (sostituire %LOCALAPPDATA% col percorso reale)."
    ))
    story.append(tip(
        "Per trovare il percorso esatto: cerca uno dei file .ttf con Esplora File, "
        "clic destro &gt; Proprieta' e annota il percorso della cartella."
    ))

    # ── 5. Installare le dipendenze Python ──
    story.append(PageBreak())
    story.append(Paragraph("5. Installare le dipendenze Python", style_h1))
    story.append(accent_line())
    story.append(step(1, "Apri il Prompt dei comandi (cmd)"))
    story.append(step(2, "Naviga nella cartella del progetto:"))
    story.append(code('cd "C:\\Users\\UTENTE\\Desktop\\Souvenir Petit Bellevue"'))
    story.append(step(3, "Installa tutti i pacchetti necessari:"))
    story.append(code("pip install -r requirements.txt"))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("I pacchetti installati saranno:", style_body))
    story.append(bullet("<b>streamlit</b> — interfaccia web"))
    story.append(bullet("<b>reportlab</b> — generazione PDF"))
    story.append(bullet("<b>pypdf</b> — merge PDF"))
    story.append(bullet("<b>PyMuPDF</b> — anteprima PDF"))
    story.append(bullet("<b>Pillow</b> — elaborazione immagini"))
    story.append(bullet("<b>numpy</b> — calcoli"))
    story.append(bullet("<b>openpyxl</b> — lettura Excel"))
    story.append(warn(
        "Se pip non viene riconosciuto, prova con: <b>python -m pip install -r requirements.txt</b>"
    ))

    # ── 6. Primo avvio ──
    story.append(Paragraph("6. Primo avvio", style_h1))
    story.append(accent_line())
    story.append(step(1, "Fai doppio clic su <b>Avvia Souvenir.bat</b>"))
    story.append(step(2, "Si apre una finestra nera del terminale — NON chiuderla"))
    story.append(step(3, 'Leggi l\'indirizzo <b>"Local URL"</b> nella finestra nera e copialo in Chrome'))
    story.append(step(4, "L'interfaccia Streamlit dovrebbe apparire"))
    story.append(Spacer(1, 2*mm))
    story.append(tip(
        'La porta puo\' variare (es. 8501, 8502...): '
        'usa sempre l\'indirizzo indicato nella finestra del terminale.'
    ))

    # ── 7. Troubleshooting ──
    story.append(Paragraph("7. Risoluzione problemi", style_h1))
    story.append(accent_line())

    problems = [
        ["Problema", "Soluzione"],
        ["python non riconosciuto", "Reinstalla Python spuntando 'Add to PATH'"],
        ["pip non riconosciuto", "Usa: python -m pip install ..."],
        ["Font non trovato (errore TTFont)", "Verifica percorso FONTS_DIR (riga 29) — deve puntare alla cartella con i 4 file .ttf"],
        ["Sfondo non trovato", "Verifica percorso ROOT (riga 24) — deve contenere 'Sfondo souvenir.pdf'"],
        ["Pagina bianca/errore Streamlit", "Chiudi tutto, cancella scripts/__pycache__/, riavvia"],
        ["Non si apre nel browser", "Controlla nella finestra nera l'indirizzo 'Local URL' e usa quello"],
        ["PDF generato vuoto/corrotto", "Controlla che Riga rossa.pdf sia nella cartella principale"],
    ]
    prob_table = Table(problems, colWidths=[55*mm, 105*mm])
    prob_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "BernhardMod-Bd"),
        ("FONTNAME", (0, 1), (-1, -1), "BernhardMod"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), CLR_TITLE),
        ("TEXTCOLOR", (0, 1), (-1, -1), CLR_BODY),
        ("BACKGROUND", (0, 0), (-1, 0), CLR_CODE_BG),
        ("BACKGROUND", (0, 1), (0, -1), HexColor("#FFF8F0")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, CLR_ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(prob_table)

    # ── 8. Aggiornare il database piatti ──
    story.append(Paragraph("8. Modificare il database piatti", style_h1))
    story.append(accent_line())
    story.append(Paragraph(
        "Il file <b>database/menu_database.json</b> contiene tutti i piatti. "
        "Per aggiungere un piatto, copia un blocco esistente e modifica i campi. "
        "Per cambiare i menu fissi (esprit/terroir), modifica la lista nel file "
        "<b>scripts/genera_souvenir.py</b> alla sezione MENU_FISSI (circa riga 185).",
        style_body
    ))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        'Formato di un piatto nel database:',
        style_body_bold
    ))
    story.append(code(
        '{<br/>'
        '&nbsp;&nbsp;"id": "nome_piatto",<br/>'
        '&nbsp;&nbsp;"nome_it": "Nome italiano",<br/>'
        '&nbsp;&nbsp;"ingredienti_it": "ingrediente1, ingrediente2",<br/>'
        '&nbsp;&nbsp;"nome_fr": "Nom francais",<br/>'
        '&nbsp;&nbsp;"ingredienti_fr": "ingredient1, ingredient2",<br/>'
        '&nbsp;&nbsp;"nome_en": "English name",<br/>'
        '&nbsp;&nbsp;"ingredienti_en": "ingredient1, ingredient2",<br/>'
        '&nbsp;&nbsp;"categoria": "menu_esprit",<br/>'
        '&nbsp;&nbsp;"prezzo_carta": 40<br/>'
        '}'
    ))

    # Build
    doc.build(story, onFirstPage=page_bg, onLaterPages=page_bg)
    print(f"Guida tecnica generata: {path}")
    return path


# ══════════════════════════════════════════════════════════════
# 2. GUIDA UTENTE (RICEVIMENTO)
# ══════════════════════════════════════════════════════════════

def genera_guida_utente():
    path = OUTPUT_DIR / "Guida_Utente_Souvenir.pdf"
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        topMargin=15*mm, bottomMargin=15*mm,
        leftMargin=18*mm, rightMargin=18*mm,
    )

    # Stili — copertina elegante + step compatti
    s_title = ParagraphStyle(
        "UTitle", fontName="Bellevue", fontSize=36, leading=44,
        textColor=CLR_TITLE, alignment=TA_CENTER, spaceAfter=4*mm,
    )
    s_sub = ParagraphStyle(
        "USub", fontName="BernhardMod-It", fontSize=13, leading=17,
        textColor=CLR_SUBTITLE, alignment=TA_CENTER, spaceAfter=8*mm,
    )
    s_step_header = ParagraphStyle(
        "UStepHeader", fontName="BernhardMod-Bd", fontSize=11, leading=14.5,
        textColor=CLR_TITLE, alignment=TA_CENTER, spaceAfter=1*mm,
    )
    s_step_desc = ParagraphStyle(
        "UStepDesc", fontName="BernhardMod", fontSize=10, leading=13.5,
        textColor=CLR_BODY, alignment=TA_CENTER, spaceAfter=0.8*mm,
    )
    s_step_detail = ParagraphStyle(
        "UStepDetail", fontName="BernhardMod-It", fontSize=8.5, leading=11,
        textColor=CLR_SUBTITLE, alignment=TA_CENTER, spaceAfter=0.5*mm,
    )
    s_warn_big = ParagraphStyle(
        "UWarnBig", fontName="BernhardMod-Bd", fontSize=9, leading=12,
        textColor=CLR_WARN_FG, backColor=CLR_WARN_BG, alignment=TA_CENTER,
        borderPadding=(2, 6, 2, 6), spaceAfter=0.5*mm,
    )
    s_note = ParagraphStyle(
        "UNote", fontName="BernhardMod-It", fontSize=8.5, leading=11,
        textColor=CLR_SUBTITLE, alignment=TA_CENTER, spaceAfter=0.5*mm,
    )

    story = []

    # ── Copertina elegante ──
    story.append(Spacer(1, 55*mm))
    story.append(Paragraph("Souvenir Petit Bellevue", s_title))
    story.append(accent_line())
    story.append(Paragraph("Come creare i souvenir per gli ospiti", s_sub))
    story.append(Spacer(1, 12*mm))
    story.append(Paragraph(
        "Questa guida spiega in 8 semplici passi come generare<br/>"
        "i menu souvenir da stampare per gli ospiti del ristorante.",
        ParagraphStyle("UIntro", fontName="BernhardMod", fontSize=12, leading=17,
                       textColor=CLR_BODY, alignment=TA_CENTER, spaceAfter=3*mm)
    ))
    story.append(PageBreak())

    # ── Pagina 2 — tutti gli 8 step, ben distribuiti ──

    def compact_step(num, title, desc, detail=None, warning=None, note=None):
        elements = []
        elements.append(HRFlowable(
            width="20%", thickness=0.4, color=CLR_ACCENT,
            spaceBefore=11*mm, spaceAfter=2.5*mm, hAlign="CENTER",
        ))
        elements.append(Paragraph(
            f'<font name="BernhardMod-Bd" size="14" color="{CLR_STEP_NUM.hexval()}">{num}</font>'
            f'&nbsp;&nbsp;{title}',
            s_step_header
        ))
        elements.append(Paragraph(desc, s_step_desc))
        if detail:
            elements.append(Paragraph(detail, s_step_detail))
        if warning:
            elements.append(Paragraph(warning, s_warn_big))
        if note:
            elements.append(Paragraph(note, s_note))
        return elements

    story += compact_step(
        1, "Avvia il programma",
        'Doppio clic su <b>"Avvia Souvenir.bat"</b> nella cartella del progetto.',
        "Si apre una finestra nera: non chiuderla!",
    )
    story += compact_step(
        2, "Apri Chrome",
        'Nella finestra nera, leggi l\'indirizzo accanto a <b>"Local URL"</b>.<br/>'
        "Copialo nella barra degli indirizzi di Chrome e premi Invio.",
        'Sara\' qualcosa come <font name="Courier" size="9" color="#4A2D6B">http://localhost:8501</font> '
        "(il numero puo' variare).",
    )
    story += compact_step(
        3, "Imposta la data",
        'Nel pannello a sinistra, seleziona la <b>"Data serata"</b>.',
    )
    story += compact_step(
        4, "Configura i tavoli",
        "Per ogni tavolo seleziona il <b>numero di ospiti</b>. Per ognuno compila: "
        "<b>Nome</b> &mdash; <b>Lingua</b> (it/fr/en) &mdash; <b>Menu</b> (esprit/terroir/carta).",
        note="Menu 'carta': seleziona i singoli piatti dal menu a tendina.",
    )
    story += compact_step(
        5, "Genera i PDF",
        'Clicca <b>"Genera tutti i PDF"</b> nel pannello a sinistra e attendi.',
    )
    story += compact_step(
        6, "Controlla l'anteprima",
        "Sotto i tavoli appare l'anteprima. Verifica nomi e piatti.",
    )
    story += compact_step(
        7, "Scarica e stampa",
        'Clicca <b>"Scarica ZIP"</b> per tutti i PDF, oppure scaricali singolarmente.',
        warning="Stampare IN UFFICIO con CARTA SPESSA — A4 orizzontale, fronte-retro, lato corto",
    )
    story += compact_step(
        8, "Chiudi",
        "Chiudi la finestra nera del terminale (o la scheda di Chrome).",
    )

    # ── Nota finale ──
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(
        width="35%", thickness=0.5, color=CLR_ACCENT,
        spaceBefore=2*mm, spaceAfter=3*mm, hAlign="CENTER",
    ))
    story.append(Paragraph(
        "In caso di problemi, contattare Pietro.",
        ParagraphStyle("UFinal", fontName="BernhardMod-It", fontSize=9,
                       leading=12, textColor=CLR_SUBTITLE, alignment=TA_CENTER)
    ))

    # Build
    doc.build(story, onFirstPage=page_bg, onLaterPages=page_bg)
    print(f"Guida utente generata: {path}")
    return path


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Generazione guide PDF...")
    genera_guida_tecnica()
    genera_guida_utente()
    print("Fatto!")
