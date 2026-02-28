"""
pdf_import.py — Estrae piatti, menu e abbinamenti vini da PDF menu usando Claude Vision.
Pipeline: PDF -> immagini PNG (PyMuPDF) -> Claude Sonnet -> JSON strutturato.
"""

import base64
import json
import re
import unicodedata

import fitz  # PyMuPDF


EXTRACTION_PROMPT = """Analizza queste immagini di un menu di ristorante fine dining.
Restituisci un JSON object con 3 chiavi: "piatti", "menu_degustazione", "abbinamenti_vini".

## PIATTI
Estrai TUTTI i piatti visibili. Per ogni piatto:
- "nome_it": nome in italiano (Title Case, non MAIUSCOLO)
- "ingredienti_it": ingredienti/descrizione in italiano
- "nome_fr": nome in francese (se presente, altrimenti "")
- "ingredienti_fr": ingredienti in francese (se presente, altrimenti "")
- "nome_en": nome in inglese (se presente, altrimenti "")
- "ingredienti_en": ingredienti in inglese (se presente, altrimenti "")
- "categoria": una tra "menu_esprit", "menu_terroir", "menu_esprit_terroir", "alla_carta"
- "prezzo_carta": prezzo numerico se indicato, altrimenti null

Regole categorie:
- Se il piatto fa parte di un menu degustazione "Esprit" (o simile), usa "menu_esprit"
- Se fa parte di un menu "Terroir" (o simile), usa "menu_terroir"
- Se appare in entrambi i menu, usa "menu_esprit_terroir"
- Se e' alla carta con prezzo proprio, usa "alla_carta"
- NON includere titoli di sezione, intestazioni, o note a pie' di pagina

## MENU DEGUSTAZIONE
Estrai i menu degustazione (percorsi a prezzo fisso). Per ogni menu:
- "id": identificativo snake_case (es. "esprit", "terroir")
- "nome": nome del menu
- "prezzo": prezzo numerico del menu (solo il numero, senza simbolo valuta)

## ABBINAMENTI VINI
Estrai tutti gli abbinamenti vini / wine pairings proposti. Per ogni abbinamento:
- "id": identificativo snake_case (es. "abbinamento_esprit_italia", "abbinamento_terroir_vitae")
- "nome": nome dell'abbinamento (es. "Abbinamenti vini Esprit")
- "sottotitolo": sottotitolo/descrizione se presente (es. "Quando la Francia e l'Italia parlano...")
- "menu_riferimento": id del menu a cui si riferisce (es. "esprit" o "terroir")
- "prezzo": prezzo numerico

Rispondi SOLO con il JSON object, senza markdown fences, senza testo aggiuntivo.
Esempio struttura:
{"piatti": [...], "menu_degustazione": [...], "abbinamenti_vini": [...]}
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
    nfkd = unicodedata.normalize("NFKD", raw)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    s = ascii_str.lower().strip()
    for art in ["il ", "la ", "lo ", "l'", "le ", "i ", "gli ", "un ", "una ",
                 "del ", "della ", "dei ", "delle "]:
        if s.startswith(art):
            s = s[len(art):]
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s


def _validate_piatti(raw: list) -> list[dict]:
    """Valida e normalizza la lista di piatti estratti."""
    VALID_CATS = {"menu_esprit", "menu_terroir", "menu_esprit_terroir", "alla_carta"}
    result = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
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
        if piatto["categoria"] not in VALID_CATS:
            piatto["categoria"] = "alla_carta"
        if piatto["prezzo_carta"] is not None:
            try:
                piatto["prezzo_carta"] = int(float(piatto["prezzo_carta"]))
            except (ValueError, TypeError):
                piatto["prezzo_carta"] = None
        result.append(piatto)
    return result


def _validate_menus(raw: list) -> list[dict]:
    """Valida menu degustazione estratti."""
    result = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        nome = (item.get("nome") or "").strip()
        if not nome:
            continue
        menu = {
            "id": (item.get("id") or _clean_id(nome)).strip(),
            "nome": nome,
            "prezzo": None,
        }
        if item.get("prezzo") is not None:
            try:
                menu["prezzo"] = int(float(item["prezzo"]))
            except (ValueError, TypeError):
                pass
        result.append(menu)
    return result


def _validate_abbinamenti(raw: list) -> list[dict]:
    """Valida abbinamenti vini estratti."""
    result = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        nome = (item.get("nome") or "").strip()
        if not nome:
            continue
        abb = {
            "id": (item.get("id") or _clean_id(nome)).strip(),
            "nome": nome,
            "sottotitolo": (item.get("sottotitolo") or "").strip() or None,
            "menu_riferimento": (item.get("menu_riferimento") or "").strip() or None,
            "prezzo": None,
        }
        if item.get("prezzo") is not None:
            try:
                abb["prezzo"] = int(float(item["prezzo"]))
            except (ValueError, TypeError):
                pass
        result.append(abb)
    return result


def build_menu_piatti_ids(piatti: list[dict], menu_id: str) -> list[str]:
    """Costruisce la lista piatti_ids per un menu dalle categorie dei piatti."""
    cat_map = {
        "esprit": {"menu_esprit", "menu_esprit_terroir"},
        "terroir": {"menu_terroir", "menu_esprit_terroir"},
    }
    cats = cat_map.get(menu_id, set())
    if not cats:
        return []
    return [p["id"] for p in piatti if p.get("categoria") in cats]


def extract_from_pdf(pdf_bytes: bytes, api_key: str) -> dict:
    """Pipeline completa: PDF -> immagini -> Claude Vision -> piatti + menu + abbinamenti."""
    from anthropic import Anthropic

    images_b64 = pdf_to_base64_images(pdf_bytes, dpi=200)
    if not images_b64:
        raise ValueError("Il PDF non contiene pagine.")

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
        max_tokens=8192,
        messages=[{"role": "user", "content": content}],
    )

    raw_text = response.content[0].text.strip()

    # Rimuovi eventuale markdown fence
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```\w*\n?", "", raw_text)
        raw_text = re.sub(r"\n?```$", "", raw_text)
        raw_text = raw_text.strip()

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude non ha restituito JSON valido: {e}\n\nRisposta:\n{raw_text[:500]}")

    if isinstance(data, list):
        # Backward compat: solo piatti
        return {
            "piatti": _validate_piatti(data),
            "menu_degustazione": [],
            "abbinamenti_vini": [],
        }

    if not isinstance(data, dict):
        raise ValueError(f"Atteso JSON object, ricevuto: {type(data).__name__}")

    piatti = _validate_piatti(data.get("piatti", []))
    menus = _validate_menus(data.get("menu_degustazione", []))
    abbinamenti = _validate_abbinamenti(data.get("abbinamenti_vini", []))

    # Auto-assegna piatti_ids ai menu
    for m in menus:
        m["piatti_ids"] = build_menu_piatti_ids(piatti, m["id"])

    return {
        "piatti": piatti,
        "menu_degustazione": menus,
        "abbinamenti_vini": abbinamenti,
    }


# Backward compat
def extract_piatti_from_pdf(pdf_bytes: bytes, api_key: str) -> list[dict]:
    """Legacy wrapper."""
    result = extract_from_pdf(pdf_bytes, api_key)
    return result["piatti"]
