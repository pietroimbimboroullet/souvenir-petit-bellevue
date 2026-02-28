"""
pdf_import.py — Estrae piatti, menu e abbinamenti vini da PDF menu usando Claude Vision.
Pipeline: PDF -> immagini PNG (PyMuPDF) -> Claude Sonnet -> JSON strutturato.
"""

import base64
import json
import re
import unicodedata

import fitz  # PyMuPDF


EXTRACTION_PROMPT = """Analizza queste immagini del menu di un ristorante fine dining.
Il ristorante propone tipicamente due menu degustazione (es. "Esprit" e "Terroir") piu' piatti alla carta.
Alcuni piatti possono apparire in ENTRAMBI i menu degustazione, e spesso sono anche ordinabili alla carta.

Restituisci un JSON object con 3 chiavi: "piatti", "menu_degustazione", "abbinamenti_vini".

## PIATTI — REGOLA FONDAMENTALE: NESSUN DUPLICATO
Ogni piatto deve comparire UNA SOLA VOLTA nella lista, anche se appare in piu' sezioni del menu.

Per capire la categoria, ragiona cosi':
1. Prima identifica QUALI piatti appartengono al menu "Esprit" e QUALI al menu "Terroir"
2. Se un piatto appare SOLO nell'Esprit → categoria "menu_esprit"
3. Se un piatto appare SOLO nel Terroir → categoria "menu_terroir"
4. Se un piatto appare in ENTRAMBI i menu → categoria "menu_esprit_terroir"
5. Se un piatto ha un prezzo individuale e non fa parte di nessun menu degustazione → categoria "alla_carta"
6. Se un piatto fa parte di un menu degustazione MA ha anche un prezzo individuale, metti comunque la categoria del menu e aggiungi il prezzo in "prezzo_carta"

Campi per ogni piatto:
- "nome_it": nome in italiano (Title Case, non MAIUSCOLO)
- "ingredienti_it": ingredienti/descrizione in italiano (la riga sotto il nome del piatto)
- "nome_fr": nome in francese (se presente, altrimenti "")
- "ingredienti_fr": ingredienti in francese (se presente, altrimenti "")
- "nome_en": nome in inglese (se presente, altrimenti "")
- "ingredienti_en": ingredienti in inglese (se presente, altrimenti "")
- "categoria": una tra "menu_esprit", "menu_terroir", "menu_esprit_terroir", "alla_carta"
- "prezzo_carta": prezzo numerico se indicato, altrimenti null

NON includere: titoli di sezione, intestazioni, note a pie' pagina, nomi dei menu stessi.
L'ordine dei piatti deve seguire la sequenza del pasto: antipasti, primi, secondi, formaggi, dessert.

## MENU DEGUSTAZIONE
Estrai i percorsi degustazione a prezzo fisso. Per ogni menu:
- "id": snake_case (es. "esprit", "terroir")
- "nome": nome del menu
- "prezzo": prezzo numerico (solo il numero)

## ABBINAMENTI VINI
Estrai gli abbinamenti vini / wine pairings. Per ogni abbinamento:
- "id": snake_case (es. "abbinamento_esprit_francia_italia")
- "nome": nome dell'abbinamento
- "sottotitolo": sottotitolo/frase descrittiva se presente, altrimenti null
- "menu_riferimento": id del menu a cui si riferisce ("esprit" o "terroir")
- "prezzo": prezzo numerico

Rispondi SOLO con il JSON object, senza markdown fences, senza testo aggiuntivo.
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


def _merge_categoria(cat_a: str, cat_b: str) -> str:
    """Unisce due categorie: se un piatto e' in esprit E terroir -> esprit_terroir."""
    cats = {cat_a, cat_b}
    if "menu_esprit_terroir" in cats:
        return "menu_esprit_terroir"
    if "menu_esprit" in cats and "menu_terroir" in cats:
        return "menu_esprit_terroir"
    # Stessa categoria o una e' alla_carta
    if "menu_esprit" in cats:
        return "menu_esprit"
    if "menu_terroir" in cats:
        return "menu_terroir"
    return cat_a


def _validate_piatti(raw: list) -> list[dict]:
    """Valida, normalizza e deduplica la lista di piatti estratti."""
    VALID_CATS = {"menu_esprit", "menu_terroir", "menu_esprit_terroir", "alla_carta"}
    seen = {}  # id -> index in result
    result = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        nome_it = (item.get("nome_it") or "").strip()
        if not nome_it:
            continue

        pid = _clean_id(nome_it)
        cat = item.get("categoria", "alla_carta")
        if cat not in VALID_CATS:
            cat = "alla_carta"

        prezzo = item.get("prezzo_carta")
        if prezzo is not None:
            try:
                prezzo = int(float(prezzo))
            except (ValueError, TypeError):
                prezzo = None

        # Deduplicazione: se gia' visto, unisci categoria e prendi prezzo se mancante
        if pid in seen:
            existing = result[seen[pid]]
            existing["categoria"] = _merge_categoria(existing["categoria"], cat)
            if existing["prezzo_carta"] is None and prezzo is not None:
                existing["prezzo_carta"] = prezzo
            # Riempi campi vuoti dal duplicato
            for lang in ["fr", "en"]:
                for field in [f"nome_{lang}", f"ingredienti_{lang}"]:
                    if not existing.get(field) and (item.get(field) or "").strip():
                        existing[field] = (item[field]).strip()
            continue

        piatto = {
            "id": pid,
            "nome_it": nome_it,
            "ingredienti_it": (item.get("ingredienti_it") or "").strip(),
            "nome_fr": (item.get("nome_fr") or "").strip(),
            "ingredienti_fr": (item.get("ingredienti_fr") or "").strip(),
            "nome_en": (item.get("nome_en") or "").strip(),
            "ingredienti_en": (item.get("ingredienti_en") or "").strip(),
            "categoria": cat,
            "prezzo_carta": prezzo,
            "ordine": len(result),
        }
        seen[pid] = len(result)
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
