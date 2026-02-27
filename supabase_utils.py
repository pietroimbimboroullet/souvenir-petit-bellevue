"""
supabase_utils.py — Client Supabase + CRUD per Souvenir Petit Bellevue
Fallback a menu_database.json se Supabase non e' configurato.
"""

import json
from pathlib import Path

_client = None
_USE_SUPABASE = False

DB_FILE = Path(__file__).resolve().parent / "database" / "menu_database.json"


def _init_client():
    """Inizializza il client Supabase da st.secrets o .streamlit/secrets.toml."""
    global _client, _USE_SUPABASE
    if _client is not None:
        return _client

    try:
        import streamlit as st
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except Exception:
        _USE_SUPABASE = False
        return None

    try:
        from supabase import create_client
        _client = create_client(url, key)
        _USE_SUPABASE = True
        return _client
    except Exception as e:
        print(f"[supabase_utils] Errore connessione Supabase: {e}")
        _USE_SUPABASE = False
        return None


def is_supabase_active():
    """True se Supabase e' configurato e raggiungibile."""
    _init_client()
    return _USE_SUPABASE


# ══════════════════════════════════════════════════════════════
# LOAD
# ══════════════════════════════════════════════════════════════

def load_piatti():
    """Carica piatti da Supabase (ordine per campo 'ordine')."""
    client = _init_client()
    if not client:
        return None
    resp = client.table("piatti").select("*").order("ordine").execute()
    return resp.data


def load_menu_degustazione():
    """Carica menu degustazione da Supabase."""
    client = _init_client()
    if not client:
        return None
    resp = client.table("menu_degustazione").select("*").execute()
    return resp.data


def load_team():
    """Carica team da Supabase."""
    client = _init_client()
    if not client:
        return None
    resp = client.table("team").select("*").order("id").execute()
    return resp.data


def load_db():
    """Compone il dict DB nel formato atteso da genera_souvenir.py.
    Prova Supabase, fallback a JSON locale."""
    piatti = load_piatti()
    if piatti is not None:
        menu_deg = load_menu_degustazione() or []
        team = load_team() or []
        # Converti prezzo_carta da stringa a int/None dove possibile
        for p in piatti:
            v = p.get("prezzo_carta")
            if v is not None:
                try:
                    p["prezzo_carta"] = int(v)
                except (ValueError, TypeError):
                    pass  # lascia stringa (es. "da 10 a 42")
            else:
                p["prezzo_carta"] = None
        return {"piatti": piatti, "menu_degustazione": menu_deg, "team": team}

    # Fallback: JSON locale
    return _load_from_json()


def _load_from_json():
    """Carica da menu_database.json."""
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════
# CRUD PIATTI
# ══════════════════════════════════════════════════════════════

def save_piatto(piatto: dict):
    """Inserisce o aggiorna un piatto (upsert by id)."""
    client = _init_client()
    if not client:
        return False
    client.table("piatti").upsert(piatto).execute()
    return True


def update_piatto(piatto_id: str, updates: dict):
    """Aggiorna campi specifici di un piatto."""
    client = _init_client()
    if not client:
        return False
    client.table("piatti").update(updates).eq("id", piatto_id).execute()
    return True


def delete_piatto(piatto_id: str):
    """Elimina un piatto per ID."""
    client = _init_client()
    if not client:
        return False
    client.table("piatti").delete().eq("id", piatto_id).execute()
    return True


def delete_all_piatti():
    """Elimina tutti i piatti dalla tabella."""
    client = _init_client()
    if not client:
        return False
    client.table("piatti").delete().neq("id", "").execute()
    return True


def reorder_piatti(ordered_ids: list):
    """Aggiorna il campo 'ordine' per tutti i piatti."""
    client = _init_client()
    if not client:
        return False
    for i, pid in enumerate(ordered_ids):
        client.table("piatti").update({"ordine": i}).eq("id", pid).execute()
    return True


# ══════════════════════════════════════════════════════════════
# CRUD MENU DEGUSTAZIONE
# ══════════════════════════════════════════════════════════════

def save_menu(menu: dict):
    """Inserisce o aggiorna un menu degustazione."""
    client = _init_client()
    if not client:
        return False
    client.table("menu_degustazione").upsert(menu).execute()
    return True


def delete_menu(menu_id: str):
    """Elimina un menu degustazione."""
    client = _init_client()
    if not client:
        return False
    client.table("menu_degustazione").delete().eq("id", menu_id).execute()
    return True


# ══════════════════════════════════════════════════════════════
# CRUD TEAM
# ══════════════════════════════════════════════════════════════

def save_team_member(member: dict):
    """Inserisce o aggiorna un membro del team."""
    client = _init_client()
    if not client:
        return False
    if "id" in member and member["id"]:
        client.table("team").update(member).eq("id", member["id"]).execute()
    else:
        m = {k: v for k, v in member.items() if k != "id"}
        client.table("team").insert(m).execute()
    return True


def delete_team_member(member_id: int):
    """Elimina un membro del team."""
    client = _init_client()
    if not client:
        return False
    client.table("team").delete().eq("id", member_id).execute()
    return True
