"""
pdf_import.py — Estrae piatti da PDF menu usando Claude Vision.
Pipeline: PDF -> immagini PNG (PyMuPDF) -> Claude Sonnet -> JSON piatti.
"""

import base64
import json
import re
import unicodedata

import fitz  # PyMuPDF


EXTRACTION_PROMPT = """Analizza queste immagini di un menu di ristorante.
Estrai TUTTI i piatti visibili e restituisci un JSON array.

Per ogni piatto restituisci un oggetto con ESATTAMENTE questi campi:
- "nome_it": nome del piatto in italiano
- "ingredienti_it": ingredienti/descrizione in italiano
- "nome_fr": nome del piatto in francese (se presente, altrimenti stringa vuota)
- "ingredienti_fr": ingredienti/descrizione in francese (se presente, altrimenti stringa vuota)
- "nome_en": nome del piatto in inglese (se presente, altrimenti stringa vuota)
- "ingredienti_en": ingredienti/descrizione in inglese (se presente, altrimenti stringa vuota)
- "categoria": una tra "menu_esprit", "menu_terroir", "menu_esprit_terroir", "alla_carta"
- "prezzo_carta": prezzo numerico se indicato, altrimenti null

Regole:
- Se il piatto fa parte di un menu degustazione chiamato "Esprit", usa categoria "menu_esprit"
- Se fa parte di un menu "Terroir", usa categoria "menu_terroir"
- Se appare in entrambi, usa "menu_esprit_terroir"
- Se e' alla carta con prezzo proprio, usa "alla_carta"
- NON includere titoli di sezione, intestazioni, o note a pie' di pagina
- I nomi dei piatti spesso sono in maiuscolo nel menu: convertili in Title Case
- Gli ingredienti sono la descrizione sotto il nome del piatto

Rispondi SOLO con il JSON array, senza markdown fences, senza testo aggiuntivo.
"""


def pdf_to_base64_images(pdf_bytes: bytes, dpi: int = 200) -> list[str]:
    """Renderizza ogni pagina del PDF come immagine PNG in base64."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    for page in doc:
        pix = page.get_pixmap(matrix=matrix)
        png_bytes = pix.tobytes("png")
        b64 = base64.standard_b64encode(png_bytes).decode("ascii")
        images.append(b64)
    doc.close()
    return images


def pdf_to_preview_images(pdf_bytes: bytes, dpi: int = 100) -> list[bytes]:
    """Renderizza pagine PDF come PNG a bassa risoluzione per anteprima."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    previews = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    for page in doc:
        pix = page.get_pixmap(matrix=matrix)
        previews.append(pix.tobytes("png"))
    doc.close()
    return previews


def _clean_id(raw: str) -> str:
    """Normalizza un nome piatto in ID snake_case senza accenti."""
    # Rimuovi accenti
    nfkd = unicodedata.normalize("NFKD", raw)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    # Lowercase
    s = ascii_str.lower().strip()
    # Rimuovi articoli comuni
    for art in ["il ", "la ", "lo ", "l'", "le ", "i ", "gli ", "un ", "una ", "del ", "della ", "dei ", "delle "]:
        if s.startswith(art):
            s = s[len(art):]
    # Sostituisci non-alfanumerici con underscore
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s


def _validate_piatti(raw: list) -> list[dict]:
    """Valida e normalizza la lista di piatti estratti."""
    REQUIRED = ["nome_it"]
    VALID_CATS = {"menu_esprit", "menu_terroir", "menu_esprit_terroir", "alla_carta"}
    result = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        # Deve avere almeno nome_it
        nome_it = (item.get("nome_it") or "").strip()
        if not nome_it:
            continue
        piatto = {
            "id": _clean_id(nome_it),
            "nome_it": nome_it,
            "ingredienti_it": (item.get("ingredienti_it") or "").strip(),
            "nome_fr": (item.get("nome_fr") or "").strip(),
            "ingredienti_fr": (item.get("ingredienti_fr") or "").strip(),
            "nome_en": (item.get("nome_en") or "").strip(),
            "ingredienti_en": (item.get("ingredienti_en") or "").strip(),
            "categoria": item.get("categoria", "alla_carta"),
            "prezzo_carta": item.get("prezzo_carta"),
            "ordine": i,
        }
        # Valida categoria
        if piatto["categoria"] not in VALID_CATS:
            piatto["categoria"] = "alla_carta"
        # Prezzo: deve essere numerico o None
        if piatto["prezzo_carta"] is not None:
            try:
                piatto["prezzo_carta"] = int(float(piatto["prezzo_carta"]))
            except (ValueError, TypeError):
                piatto["prezzo_carta"] = None
        result.append(piatto)
    return result


def extract_piatti_from_pdf(pdf_bytes: bytes, api_key: str) -> list[dict]:
    """Pipeline completa: PDF -> immagini -> Claude Vision -> piatti validati."""
    from anthropic import Anthropic

    images_b64 = pdf_to_base64_images(pdf_bytes, dpi=200)
    if not images_b64:
        raise ValueError("Il PDF non contiene pagine.")

    # Costruisci messaggio con tutte le immagini
    content = []
    for b64 in images_b64:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": b64,
            },
        })
    content.append({"type": "text", "text": EXTRACTION_PROMPT})

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": content}],
    )

    # Estrai testo dalla risposta
    raw_text = response.content[0].text.strip()

    # Rimuovi eventuale markdown fence
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```\w*\n?", "", raw_text)
        raw_text = re.sub(r"\n?```$", "", raw_text)
        raw_text = raw_text.strip()

    # Parse JSON
    try:
        piatti_raw = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude non ha restituito JSON valido: {e}\n\nRisposta:\n{raw_text[:500]}")

    if not isinstance(piatti_raw, list):
        raise ValueError(f"Atteso JSON array, ricevuto: {type(piatti_raw).__name__}")

    return _validate_piatti(piatti_raw)
