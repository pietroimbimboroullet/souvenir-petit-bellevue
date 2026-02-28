"""
Gestione Menu — CRUD piatti, menu degustazione e team via Supabase.
Fallback read-only da JSON se Supabase non configurato.
"""

import streamlit as st
import pandas as pd
from ui_helpers import apply_ui
from supabase_utils import (
    is_supabase_active, load_piatti, load_menu_degustazione, load_team,
    save_piatto, update_piatto, delete_piatto, delete_all_piatti, reorder_piatti,
    save_menu, delete_menu, delete_all_menus,
    save_team_member, delete_team_member,
    _load_from_json,
)
from pdf_import import extract_from_pdf, pdf_to_preview_images

st.set_page_config(page_title="Gestione Menu", layout="wide")
apply_ui()
st.title("Gestione Menu")
st.markdown('<p class="title-caption">Piatti, menu degustazione e team</p>', unsafe_allow_html=True)

supabase_ok = is_supabase_active()
with st.sidebar:
    if supabase_ok:
        st.success("Supabase connesso", icon=":material/cloud_done:")
    else:
        st.warning("Sola lettura (JSON locale)", icon=":material/cloud_off:")

# ══════════════════════════════════════════════════════════════
# DATI
# ══════════════════════════════════════════════════════════════

def _reload():
    """Ricarica dati da Supabase o JSON."""
    if supabase_ok:
        return load_piatti() or [], load_menu_degustazione() or [], load_team() or []
    db = _load_from_json()
    return db["piatti"], db.get("menu_degustazione", []), db.get("team", [])


if "data_loaded" not in st.session_state:
    st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
    st.session_state.data_loaded = True

CATEGORIE = ["menu_esprit", "menu_terroir", "alla_carta"]


# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════

tab_import, tab_piatti, tab_menu, tab_team = st.tabs(
    ["Importa da PDF", "Piatti", "Menu degustazione", "Team"]
)

# ── TAB IMPORT ─────────────────────────────────────────────
with tab_import:
    if not supabase_ok:
        st.info("Import non disponibile senza Supabase.")
    else:
        # API key check
        api_key = None
        try:
            api_key = st.secrets["anthropic"]["api_key"]
            if api_key == "YOUR_ANTHROPIC_API_KEY_HERE":
                api_key = None
        except (KeyError, Exception):
            pass

        if not api_key:
            st.error("API key Anthropic non configurata. Aggiungi `[anthropic] api_key` in `.streamlit/secrets.toml`.")
        else:
            st.markdown("Carica il PDF del menu per estrarre automaticamente **piatti**, **menu degustazione** e **abbinamenti vini**.")

            uploaded_pdf = st.file_uploader(
                "Carica il PDF del menu",
                type=["pdf"],
                key="pdf_import_uploader",
            )

            if uploaded_pdf:
                pdf_bytes = uploaded_pdf.read()

                # Anteprima pagine
                with st.container(border=True):
                    st.markdown("##### Anteprima")
                    previews = pdf_to_preview_images(pdf_bytes, dpi=100)
                    cols = st.columns(min(len(previews), 4))
                    for i, png in enumerate(previews):
                        with cols[i % len(cols)]:
                            st.image(png, caption=f"Pagina {i + 1}", use_container_width=True)

                # Bottone estrazione
                if st.button("Estrai con AI", type="primary", key="btn_extract_pdf", use_container_width=True):
                    with st.spinner("Claude sta analizzando il menu..."):
                        try:
                            result = extract_from_pdf(pdf_bytes, api_key)
                            st.session_state.pdf_extracted = result["piatti"]
                            st.session_state.pdf_menus = result["menu_degustazione"]
                            st.session_state.pdf_abbinamenti = result["abbinamenti_vini"]
                            n_p = len(result["piatti"])
                            n_m = len(result["menu_degustazione"])
                            n_a = len(result["abbinamenti_vini"])
                            st.success(f"Estratti **{n_p} piatti**, **{n_m} menu**, **{n_a} abbinamenti vini**")
                        except Exception as e:
                            st.error(f"Errore estrazione: {e}")

                # ── RISULTATI ──────────────────────────────────────
                has_results = (
                    "pdf_extracted" in st.session_state and st.session_state.pdf_extracted
                )

                if has_results:
                    items = st.session_state.pdf_extracted
                    menus = st.session_state.get("pdf_menus", [])
                    abbinamenti = st.session_state.get("pdf_abbinamenti", [])

                    st.divider()

                    # ── PIATTI: ordine e rimozione ──
                    with st.container(border=True):
                        st.markdown("##### Piatti estratti")
                        st.caption(f"{len(items)} piatti — usa le frecce per riordinare")

                        for idx, p in enumerate(items):
                            c_num, c_name, c_price, c_actions = st.columns([0.4, 4, 1, 1.5])
                            with c_num:
                                st.markdown(f"**{idx+1}**")
                            with c_name:
                                st.markdown(f"**{p.get('nome_it', '?')}**")
                                if p.get("ingredienti_it"):
                                    st.caption(p["ingredienti_it"])
                            with c_price:
                                if p.get("prezzo_carta"):
                                    st.caption(f"{p['prezzo_carta']} EUR")
                            with c_actions:
                                bc1, bc2, bc3 = st.columns(3)
                                with bc1:
                                    if idx > 0 and st.button("↑", key=f"imp_up_{idx}"):
                                        items[idx], items[idx - 1] = items[idx - 1], items[idx]
                                        st.rerun()
                                with bc2:
                                    if idx < len(items) - 1 and st.button("↓", key=f"imp_dn_{idx}"):
                                        items[idx], items[idx + 1] = items[idx + 1], items[idx]
                                        st.rerun()
                                with bc3:
                                    if st.button("✕", key=f"imp_rm_{idx}"):
                                        items.pop(idx)
                                        st.rerun()

                    # ── MODIFICA CONTENUTI (data_editor) ──
                    with st.expander("Modifica contenuti piatti", expanded=False):
                        df = pd.DataFrame(items)
                        column_order = ["id", "nome_it", "ingredienti_it", "nome_fr", "ingredienti_fr",
                                        "nome_en", "ingredienti_en", "prezzo_carta"]
                        for col in column_order:
                            if col not in df.columns:
                                df[col] = ""
                        df = df[column_order]

                        edited_df = st.data_editor(
                            df,
                            num_rows="dynamic",
                            use_container_width=True,
                            column_config={
                                "id": st.column_config.TextColumn("ID", width="medium"),
                                "nome_it": st.column_config.TextColumn("Nome IT", width="large"),
                                "ingredienti_it": st.column_config.TextColumn("Ingredienti IT", width="large"),
                                "nome_fr": st.column_config.TextColumn("Nome FR", width="large"),
                                "ingredienti_fr": st.column_config.TextColumn("Ingredienti FR", width="large"),
                                "nome_en": st.column_config.TextColumn("Nome EN", width="large"),
                                "ingredienti_en": st.column_config.TextColumn("Ingredienti EN", width="large"),
                                "prezzo_carta": st.column_config.NumberColumn("Prezzo", width="small"),
                            },
                            key="pdf_piatti_editor",
                        )

                    # Helper: mappa nome_it -> id dai piatti estratti
                    _pid_map = {p["nome_it"]: p["id"] for p in items}

                    # ── MENU DEGUSTAZIONE ESTRATTI ──
                    with st.container(border=True):
                        st.markdown("##### Menu degustazione")
                        if menus:
                            for m in menus:
                                mc1, mc2 = st.columns([3, 1])
                                with mc1:
                                    st.markdown(f"**{m['nome']}** `{m['id']}`")
                                    pids = m.get("piatti_ids", [])
                                    if pids:
                                        pnames = [p["nome_it"] for p in items if p["id"] in pids]
                                        st.caption(" → ".join(pnames) if pnames else ", ".join(pids))
                                    else:
                                        st.caption("_Nessun piatto associato_")
                                with mc2:
                                    if m.get("prezzo"):
                                        st.metric("Prezzo", f"{m['prezzo']} EUR")
                        else:
                            st.info("Nessun menu degustazione estratto dal PDF.")

                    # ── ABBINAMENTI VINI ──
                    with st.container(border=True):
                        st.markdown("##### Abbinamenti vini")
                        if abbinamenti:
                            for a in abbinamenti:
                                ac1, ac2 = st.columns([3, 1])
                                with ac1:
                                    sub = f" — *{a['sottotitolo']}*" if a.get("sottotitolo") else ""
                                    rif = f" (rif: `{a['menu_riferimento']}`)" if a.get("menu_riferimento") else ""
                                    st.markdown(f"**{a['nome']}**{sub}{rif}")
                                with ac2:
                                    if a.get("prezzo"):
                                        st.metric("Prezzo", f"{a['prezzo']} EUR")
                        else:
                            st.caption("Nessun abbinamento vini estratto dal PDF.")

                    # ── SALVATAGGIO ──
                    st.divider()
                    import_mode = st.radio(
                        "Modalita' di importazione:",
                        ["Sostituisci TUTTO (piatti + menu)", "Aggiungi ai piatti esistenti"],
                        key="pdf_import_mode",
                        horizontal=True,
                    )

                    if import_mode == "Sostituisci TUTTO (piatti + menu)":
                        st.warning("Tutti i piatti e menu esistenti verranno eliminati e sostituiti.")

                    if st.button("Conferma e salva tutto", type="primary", key="btn_save_imported", use_container_width=True):
                        valid_rows = edited_df.dropna(subset=["id", "nome_it"])
                        valid_rows = valid_rows[valid_rows["id"].str.strip() != ""]
                        valid_rows = valid_rows[valid_rows["nome_it"].str.strip() != ""]

                        if valid_rows.empty:
                            st.error("Nessun piatto valido da salvare.")
                        else:
                            with st.spinner("Salvataggio in corso..."):
                                is_replace = import_mode.startswith("Sostituisci")

                                # 1. Piatti
                                if is_replace:
                                    delete_all_piatti()

                                saved_piatti = 0
                                for ordine_idx, (_, row) in enumerate(valid_rows.iterrows()):
                                    # prezzo_carta: gestisci NaN, stringhe vuote, etc.
                                    prezzo_raw = row.get("prezzo_carta")
                                    prezzo_val = None
                                    if pd.notna(prezzo_raw) and str(prezzo_raw).strip():
                                        try:
                                            prezzo_val = int(float(prezzo_raw))
                                        except (ValueError, TypeError):
                                            prezzo_val = str(prezzo_raw).strip()

                                    piatto = {
                                        "id": str(row["id"]).strip(),
                                        "nome_it": str(row["nome_it"]).strip(),
                                        "ingredienti_it": str(row.get("ingredienti_it", "")).strip(),
                                        "nome_fr": str(row.get("nome_fr", "")).strip(),
                                        "ingredienti_fr": str(row.get("ingredienti_fr", "")).strip(),
                                        "nome_en": str(row.get("nome_en", "")).strip(),
                                        "ingredienti_en": str(row.get("ingredienti_en", "")).strip(),
                                        "categoria": "alla_carta",
                                        "prezzo_carta": prezzo_val,
                                        "ordine": ordine_idx,
                                    }
                                    if save_piatto(piatto):
                                        saved_piatti += 1

                                # 2. Menu degustazione + abbinamenti
                                saved_menus = 0
                                if is_replace:
                                    delete_all_menus()

                                for m in menus:
                                    menu_obj = {
                                        "id": m["id"],
                                        "nome": m["nome"],
                                        "prezzo": m.get("prezzo"),
                                        "piatti_ids": m.get("piatti_ids", []),
                                    }
                                    if save_menu(menu_obj):
                                        saved_menus += 1

                                for a in abbinamenti:
                                    abb_obj = {
                                        "id": a["id"],
                                        "nome": a["nome"],
                                        "sottotitolo": a.get("sottotitolo"),
                                        "menu_riferimento": a.get("menu_riferimento"),
                                        "prezzo": a.get("prezzo"),
                                    }
                                    if save_menu(abb_obj):
                                        saved_menus += 1

                            st.success(f"Salvati **{saved_piatti} piatti** e **{saved_menus} menu/abbinamenti** su Supabase!")

                            for k in ["pdf_extracted", "pdf_menus", "pdf_abbinamenti"]:
                                st.session_state.pop(k, None)
                            st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                            st.rerun()


# ── TAB PIATTI ──────────────────────────────────────────────
with tab_piatti:
    piatti = st.session_state.piatti

    if supabase_ok:
        with st.expander("Aggiungi piatto", expanded=False):
            with st.form("add_piatto", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    new_id = st.text_input("ID (univoco, snake_case)", key="new_p_id")
                    new_nome_it = st.text_input("Nome IT", key="new_p_nome_it")
                    new_ingr_it = st.text_input("Ingredienti IT", key="new_p_ingr_it")
                    new_nome_fr = st.text_input("Nome FR", key="new_p_nome_fr")
                    new_ingr_fr = st.text_input("Ingredienti FR", key="new_p_ingr_fr")
                with c2:
                    new_nome_en = st.text_input("Nome EN", key="new_p_nome_en")
                    new_ingr_en = st.text_input("Ingredienti EN", key="new_p_ingr_en")
                    new_prezzo = st.text_input("Prezzo carta", key="new_p_prezzo")
                    new_ordine = st.number_input("Ordine", value=len(piatti), key="new_p_ordine")

                if st.form_submit_button("Salva piatto"):
                    if not new_id or not new_nome_it:
                        st.error("ID e Nome IT sono obbligatori")
                    else:
                        piatto = {
                            "id": new_id.strip().lower().replace(" ", "_"),
                            "nome_it": new_nome_it, "ingredienti_it": new_ingr_it,
                            "nome_fr": new_nome_fr, "ingredienti_fr": new_ingr_fr,
                            "nome_en": new_nome_en, "ingredienti_en": new_ingr_en,
                            "categoria": "alla_carta",
                            "prezzo_carta": new_prezzo if new_prezzo else None,
                            "ordine": int(new_ordine),
                        }
                        if save_piatto(piatto):
                            st.success(f"Piatto '{new_id}' salvato!")
                            st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                            st.rerun()

    # Lista piatti
    st.subheader(f"Piatti ({len(piatti)})")

    for idx, p in enumerate(piatti):
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            with c1:
                st.markdown(f"**{p.get('nome_it', '')}** `{p['id']}`")
                st.caption(p.get("ingredienti_it", ""))
            with c2:
                fr = p.get("nome_fr", "")
                en = p.get("nome_en", "")
                st.caption(f"FR: {fr} | EN: {en}")
            with c3:
                if p.get("prezzo_carta"):
                    st.caption(f"{p.get('prezzo_carta', '-')} EUR")
            with c4:
                if supabase_ok:
                    col_up, col_down, col_del = st.columns(3)
                    with col_up:
                        if idx > 0 and st.button("↑", key=f"up_{p['id']}", help="Sposta su"):
                            ids = [x["id"] for x in piatti]
                            ids[idx], ids[idx - 1] = ids[idx - 1], ids[idx]
                            reorder_piatti(ids)
                            st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                            st.rerun()
                    with col_down:
                        if idx < len(piatti) - 1 and st.button("↓", key=f"dn_{p['id']}", help="Sposta giu'"):
                            ids = [x["id"] for x in piatti]
                            ids[idx], ids[idx + 1] = ids[idx + 1], ids[idx]
                            reorder_piatti(ids)
                            st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                            st.rerun()
                    with col_del:
                        if st.button("✕", key=f"del_{p['id']}", help="Elimina"):
                            delete_piatto(p["id"])
                            st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                            st.rerun()

            # Modifica inline
            if supabase_ok:
                with st.expander("Modifica", expanded=False):
                    with st.form(f"edit_{p['id']}"):
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            e_nome_it = st.text_input("Nome IT", value=p.get("nome_it", ""), key=f"e_ni_{p['id']}")
                            e_ingr_it = st.text_input("Ingredienti IT", value=p.get("ingredienti_it", ""), key=f"e_ii_{p['id']}")
                            e_nome_fr = st.text_input("Nome FR", value=p.get("nome_fr", ""), key=f"e_nf_{p['id']}")
                            e_ingr_fr = st.text_input("Ingredienti FR", value=p.get("ingredienti_fr", ""), key=f"e_if_{p['id']}")
                        with ec2:
                            e_nome_en = st.text_input("Nome EN", value=p.get("nome_en", ""), key=f"e_ne_{p['id']}")
                            e_ingr_en = st.text_input("Ingredienti EN", value=p.get("ingredienti_en", ""), key=f"e_ie_{p['id']}")
                            e_prezzo = st.text_input("Prezzo", value=str(p.get("prezzo_carta", "") or ""), key=f"e_p_{p['id']}")

                        if st.form_submit_button("Aggiorna"):
                            updates = {
                                "nome_it": e_nome_it, "ingredienti_it": e_ingr_it,
                                "nome_fr": e_nome_fr, "ingredienti_fr": e_ingr_fr,
                                "nome_en": e_nome_en, "ingredienti_en": e_ingr_en,
                                "prezzo_carta": e_prezzo if e_prezzo else None,
                            }
                            update_piatto(p["id"], updates)
                            st.success("Aggiornato!")
                            st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                            st.rerun()

# ── TAB MENU DEGUSTAZIONE ──────────────────────────────────
with tab_menu:
    menu_list = st.session_state.menu_deg
    piatti_all = st.session_state.piatti
    piatti_ids_all = [p["id"] for p in piatti_all]
    piatti_labels = {p["id"]: p.get("nome_it", p["id"]) for p in piatti_all}

    st.subheader(f"Menu degustazione ({len(menu_list)})")

    for m in menu_list:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                subtitle = f" — *{m.get('sottotitolo', '')}*" if m.get("sottotitolo") else ""
                st.markdown(f"**{m.get('nome', '')}** `{m['id']}`{subtitle}")
                prezzo = m.get("prezzo")
                rif = m.get("menu_riferimento")
                info = []
                if prezzo:
                    info.append(f"{prezzo} EUR")
                if rif:
                    info.append(f"rif: {rif}")
                if info:
                    st.caption(" | ".join(info))

                # Piatti associati
                pids = m.get("piatti_ids") or []
                if pids:
                    names = [piatti_labels.get(pid, pid) for pid in pids]
                    st.caption("Piatti: " + " → ".join(names))
            with c2:
                if supabase_ok:
                    if st.button("Elimina", key=f"del_menu_{m['id']}"):
                        delete_menu(m["id"])
                        st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                        st.rerun()

            # Modifica piatti del menu
            if supabase_ok:
                with st.expander("Modifica", expanded=False):
                    with st.form(f"edit_menu_{m['id']}"):
                        em_nome = st.text_input("Nome", value=m.get("nome", ""), key=f"em_n_{m['id']}")
                        em_sub = st.text_input("Sottotitolo", value=m.get("sottotitolo", "") or "", key=f"em_s_{m['id']}")
                        em_rif = st.text_input("Menu riferimento", value=m.get("menu_riferimento", "") or "", key=f"em_r_{m['id']}")
                        em_prezzo = st.number_input("Prezzo", value=m.get("prezzo") or 0, key=f"em_p_{m['id']}")
                        current_pids = m.get("piatti_ids") or []
                        em_piatti = st.multiselect(
                            "Piatti (in ordine)",
                            options=piatti_ids_all,
                            default=[pid for pid in current_pids if pid in piatti_ids_all],
                            format_func=lambda x: piatti_labels.get(x, x),
                            key=f"em_pl_{m['id']}",
                        )
                        if st.form_submit_button("Aggiorna menu"):
                            updated = {
                                "id": m["id"],
                                "nome": em_nome,
                                "sottotitolo": em_sub or None,
                                "menu_riferimento": em_rif or None,
                                "prezzo": int(em_prezzo) if em_prezzo else None,
                                "piatti_ids": em_piatti if em_piatti else None,
                            }
                            save_menu(updated)
                            st.success("Menu aggiornato!")
                            st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                            st.rerun()

    # Aggiungi menu
    if supabase_ok:
        with st.expander("Aggiungi menu degustazione", expanded=False):
            with st.form("add_menu", clear_on_submit=True):
                nm_id = st.text_input("ID", key="nm_id")
                nm_nome = st.text_input("Nome", key="nm_nome")
                nm_sub = st.text_input("Sottotitolo", key="nm_sub")
                nm_rif = st.text_input("Menu riferimento", key="nm_rif")
                nm_prezzo = st.number_input("Prezzo", value=0, key="nm_prezzo")
                nm_piatti = st.multiselect(
                    "Piatti",
                    options=piatti_ids_all,
                    format_func=lambda x: piatti_labels.get(x, x),
                    key="nm_piatti",
                )
                if st.form_submit_button("Salva menu"):
                    if not nm_id or not nm_nome:
                        st.error("ID e Nome sono obbligatori")
                    else:
                        new_menu = {
                            "id": nm_id.strip().lower().replace(" ", "_"),
                            "nome": nm_nome,
                            "sottotitolo": nm_sub or None,
                            "menu_riferimento": nm_rif or None,
                            "prezzo": int(nm_prezzo) if nm_prezzo else None,
                            "piatti_ids": nm_piatti if nm_piatti else None,
                        }
                        save_menu(new_menu)
                        st.success("Menu salvato!")
                        st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                        st.rerun()

# ── TAB TEAM ────────────────────────────────────────────────
with tab_team:
    team = st.session_state.team
    st.subheader(f"Team ({len(team)})")

    for t in team:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{t.get('nome', '')}** — {t.get('ruolo', '')}")
            with c2:
                if supabase_ok:
                    if st.button("Elimina", key=f"del_team_{t.get('id', '')}"):
                        delete_team_member(t["id"])
                        st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                        st.rerun()

            if supabase_ok:
                with st.expander("Modifica", expanded=False):
                    with st.form(f"edit_team_{t.get('id', '')}"):
                        et_nome = st.text_input("Nome", value=t.get("nome", ""), key=f"et_n_{t.get('id', '')}")
                        et_ruolo = st.text_input("Ruolo", value=t.get("ruolo", ""), key=f"et_r_{t.get('id', '')}")
                        if st.form_submit_button("Aggiorna"):
                            save_team_member({"id": t["id"], "nome": et_nome, "ruolo": et_ruolo})
                            st.success("Aggiornato!")
                            st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                            st.rerun()

    if supabase_ok:
        with st.expander("Aggiungi membro", expanded=False):
            with st.form("add_team", clear_on_submit=True):
                nt_nome = st.text_input("Nome", key="nt_nome")
                nt_ruolo = st.text_input("Ruolo", key="nt_ruolo")
                if st.form_submit_button("Salva"):
                    if not nt_nome or not nt_ruolo:
                        st.error("Nome e Ruolo sono obbligatori")
                    else:
                        save_team_member({"nome": nt_nome, "ruolo": nt_ruolo})
                        st.success("Membro aggiunto!")
                        st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
                        st.rerun()

# ── REFRESH ──
st.divider()
if st.button("Ricarica dati", use_container_width=True):
    st.session_state.piatti, st.session_state.menu_deg, st.session_state.team = _reload()
    st.session_state.data_loaded = True
    st.rerun()
