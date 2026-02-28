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
Il ristorante propone menu degustazione (percorsi a prezzo fisso) e piatti alla carta.

Restituisci un JSON object con 3 chiavi: "piatti", "menu_degustazione", "abbinamenti_vini".

## PIATTI
Estrai TUTTI i piatti visibili, SENZA DUPLICATI. Ogni piatto una sola volta.
NON includere titoli di sezione, intestazioni, note a pie' pagina, nomi dei menu.

### REGOLA MAIUSCOLE/MINUSCOLE (FONDAMENTALE)
I menu PDF spesso stampano i nomi dei piatti in TUTTO MAIUSCOLO.
Tu DEVI convertirli in capitalizzazione italiana corretta:
- Solo la PRIMA lettera della frase maiuscola, il resto minuscolo
- Eccezione: nomi propri (marchi, luoghi, persone) mantengono la maiuscola
- Articoli, preposizioni, congiunzioni SEMPRE minuscoli (tranne a inizio nome)
Esempi CORRETTI: "Le animelle", "Risotto al cavolo viola", "Spaghettoni Martelli", "Zuppa del bosco"
Esempi SBAGLIATI: "Le Animelle", "RISOTTO AL CAVOLO VIOLA", "Spaghettoni martelli"
Gli ingredienti vanno SEMPRE tutto minuscolo (es. "polenta, zucca e amaretto").

Campi per ogni piatto:
- "nome_it": nome in italiano (vedi regola maiuscole sopra)
- "ingredienti_it": ingredienti/descrizione in italiano, tutto minuscolo
- "nome_fr": nome in francese (stessa regola maiuscole dell'italiano, se presente, altrimenti "")
- "ingredienti_fr": ingredienti in francese, tutto minuscolo (se presente, altrimenti "")
- "nome_en": nome in inglese (stessa regola: solo prima lettera maiuscola + nomi propri, se presente, altrimenti "")
- "ingredienti_en": ingredienti in inglese, tutto minuscolo (se presente, altrimenti "")
- "prezzo_carta": prezzo numerico se indicato accanto al piatto, altrimenti null

Ordina seguendo la sequenza del pasto: antipasti, primi, secondi, formaggi, dessert.

## MENU DEGUSTAZIONE — FONDAMENTALE
I menu degustazione sono percorsi a prezzo fisso composti da una selezione di piatti.
Lo STESSO piatto puo' apparire in piu' menu (es. il carrello formaggi o un dessert possono essere sia nel menu Esprit che nel Terroir).

Per ogni menu:
- "id": snake_case (es. "esprit", "terroir")
- "nome": nome del menu
- "prezzo": prezzo numerico del percorso (solo il numero)
- "piatti": lista ORDINATA dei nomi italiani dei piatti che compongono questo menu, esattamente come appaiono nel PDF. Questi devono corrispondere ai "nome_it" della lista piatti.

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


# Parole italiane che devono restare minuscole (articoli, preposizioni, congiunzioni)
_IT_LOWER = {
    "il", "lo", "la", "i", "gli", "le", "un", "una", "uno",
    "di", "del", "dello", "della", "dei", "degli", "delle",
    "a", "al", "allo", "alla", "ai", "agli", "alle",
    "da", "dal", "dallo", "dalla", "dai", "dagli", "dalle",
    "in", "nel", "nello", "nella", "nei", "negli", "nelle",
    "su", "sul", "sullo", "sulla", "sui", "sugli", "sulle",
    "con", "col", "per", "tra", "fra",
    "e", "ed", "o", "od", "ma",
}

# Parole francesi
_FR_LOWER = {
    "le", "la", "les", "l", "un", "une", "des",
    "de", "du", "d", "au", "aux", "à",
    "en", "dans", "sur", "sous", "par", "pour",
    "et", "ou", "mais", "ni",
}

# Parole inglesi
_EN_LOWER = {
    "the", "a", "an",
    "of", "in", "on", "at", "to", "for", "with", "from", "by",
    "and", "or", "but", "nor",
}


def _smart_capitalize(text: str, lang: str = "it") -> str:
    """Converte ALL CAPS o Title Case in capitalizzazione italiana corretta.

    Prima lettera maiuscola, resto minuscolo. Nomi propri preservati
    solo se il testo originale li distingueva (mixed case).
    """
    if not text or len(text) < 2:
        return text

    words = text.split()
    alpha_words = [w for w in words if any(c.isalpha() for c in w)]
    if not alpha_words:
        return text

    stop = _IT_LOWER if lang == "it" else (_FR_LOWER if lang == "fr" else _EN_LOWER)

    # Rileva ALL CAPS (es. "LE ANIMELLE")
    all_caps = all(
        all(c.isupper() or not c.isalpha() for c in w)
        for w in alpha_words
    )

    if all_caps:
        # ALL CAPS: tutto minuscolo, prima lettera maiuscola
        lowered = text.lower()
        return lowered[0].upper() + lowered[1:]

    # Rileva Title Case: 3+ parole con la maggior parte capitalizzata,
    # oppure 2 parole dove la prima è un articolo/preposizione
    cap_count = sum(1 for w in alpha_words if w[0].isupper())
    title_like = False
    if len(alpha_words) >= 3 and cap_count >= len(alpha_words) * 0.7:
        title_like = True
    elif len(alpha_words) == 2:
        # 2 parole: solo se la prima è articolo/prep e la seconda è capitalizzata
        first_clean = re.split(r"['\u2019]", alpha_words[0])[0].lower()
        if first_clean in stop and alpha_words[1][0].isupper():
            title_like = True

    # Caso speciale: parola con apostrofo tipo "L'Animella" (1 token)
    if not all_caps and not title_like and len(words) == 1:
        w = words[0]
        if "'" in w or "\u2019" in w:
            parts = re.split(r"['\u2019]", w, maxsplit=1)
            if (len(parts) == 2 and parts[1]
                    and parts[1][0].isupper() and not parts[1].isupper()):
                sep = "'" if "'" in w else "\u2019"
                prefix = parts[0][0].upper() + parts[0][1:].lower() if len(parts[0]) > 1 else parts[0].upper()
                return prefix + sep + parts[1].lower()

    if not title_like:
        return text  # Già corretto, non toccare

    # Title Case: sentence case (prima lettera maiuscola, resto minuscolo)
    result_words = []
    for i, w in enumerate(words):
        # Gestisci apostrofi (L'Animella -> L'animella)
        if "'" in w or "\u2019" in w:
            parts = re.split(r"['\u2019]", w, maxsplit=1)
            if len(parts) == 2:
                sep = "'" if "'" in w else "\u2019"
                if i == 0:
                    prefix = parts[0][0].upper() + parts[0][1:].lower() if len(parts[0]) > 1 else parts[0].upper()
                    result_words.append(prefix + sep + parts[1].lower())
                else:
                    result_words.append(parts[0].lower() + sep + parts[1].lower())
                continue

        if i == 0:
            result_words.append(w[0].upper() + w[1:].lower() if len(w) > 1 else w.upper())
        else:
            result_words.append(w.lower())

    return " ".join(result_words)


def _smart_capitalize_ingredients(text: str) -> str:
    """Ingredienti: tutto minuscolo, tranne nomi propri evidenti."""
    if not text:
        return text
    # Se tutto maiuscolo o Title Case, converti a minuscolo
    if text.isupper() or (len(text) > 3 and text == text.title()):
        return text.lower()
    # Se la prima lettera è maiuscola ma il resto è mixed, metti minuscolo
    return text[0].lower() + text[1:] if text[0].isupper() else text


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
    """Valida, normalizza e deduplica la lista di piatti estratti."""
    seen = {}  # id -> index in result
    result = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        nome_it = (item.get("nome_it") or "").strip()
        if not nome_it:
            continue

        pid = _clean_id(nome_it)

        prezzo = item.get("prezzo_carta")
        if prezzo is not None:
            try:
                prezzo = int(float(prezzo))
            except (ValueError, TypeError):
                prezzo = None

        # Deduplicazione
        if pid in seen:
            existing = result[seen[pid]]
            if existing["prezzo_carta"] is None and prezzo is not None:
                existing["prezzo_carta"] = prezzo
            for lang in ["fr", "en"]:
                for field in [f"nome_{lang}", f"ingredienti_{lang}"]:
                    if not existing.get(field) and (item.get(field) or "").strip():
                        existing[field] = (item[field]).strip()
            continue

        piatto = {
            "id": pid,
            "nome_it": _smart_capitalize(nome_it, "it"),
            "ingredienti_it": _smart_capitalize_ingredients((item.get("ingredienti_it") or "").strip()),
            "nome_fr": _smart_capitalize((item.get("nome_fr") or "").strip(), "fr"),
            "ingredienti_fr": _smart_capitalize_ingredients((item.get("ingredienti_fr") or "").strip()),
            "nome_en": _smart_capitalize((item.get("nome_en") or "").strip(), "en"),
            "ingredienti_en": _smart_capitalize_ingredients((item.get("ingredienti_en") or "").strip()),
            "prezzo_carta": prezzo,
            "ordine": len(result),
        }
        seen[pid] = len(result)
        result.append(piatto)
    return result


def _validate_menus(raw: list, piatti: list[dict]) -> list[dict]:
    """Valida menu degustazione estratti e risolve piatti_ids dai nomi."""
    # Mappa nome_it (lowercase) -> id per risolvere i nomi piatti
    nome_to_id = {}
    for p in piatti:
        nome_to_id[p["nome_it"].lower().strip()] = p["id"]
        # Anche senza articolo
        nome_to_id[_clean_id(p["nome_it"])] = p["id"]

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
            "piatti_ids": [],
        }
        if item.get("prezzo") is not None:
            try:
                menu["prezzo"] = int(float(item["prezzo"]))
            except (ValueError, TypeError):
                pass

        # Risolvi nomi piatti -> ID
        raw_piatti = item.get("piatti", [])
        if isinstance(raw_piatti, list):
            for nome_piatto in raw_piatti:
                if not isinstance(nome_piatto, str):
                    continue
                nome_lower = nome_piatto.strip().lower()
                pid = nome_to_id.get(nome_lower)
                if not pid:
                    pid = nome_to_id.get(_clean_id(nome_piatto))
                if not pid:
                    # Fuzzy: cerca contenimento
                    for key, val in nome_to_id.items():
                        if nome_lower in key or key in nome_lower:
                            pid = val
                            break
                if pid and pid not in menu["piatti_ids"]:
                    menu["piatti_ids"].append(pid)

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
        return {
            "piatti": _validate_piatti(data),
            "menu_degustazione": [],
            "abbinamenti_vini": [],
        }

    if not isinstance(data, dict):
        raise ValueError(f"Atteso JSON object, ricevuto: {type(data).__name__}")

    piatti = _validate_piatti(data.get("piatti", []))
    menus = _validate_menus(data.get("menu_degustazione", []), piatti)
    abbinamenti = _validate_abbinamenti(data.get("abbinamenti_vini", []))

    return {
        "piatti": piatti,
        "menu_degustazione": menus,
        "abbinamenti_vini": abbinamenti,
    }
