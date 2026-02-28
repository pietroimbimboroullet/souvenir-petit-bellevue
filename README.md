# Souvenir Menu - Le Petit Bellevue

Generatore automatico di souvenir menu in formato PDF per gli ospiti del ristorante gastronomico **Le Petit Bellevue** del **Bellevue Hotel & Spa** di Cogne, Valle d'Aosta.

## Descrizione

Il progetto produce un PDF in formato A4 orizzontale, piegato a metà, che gli ospiti possono portare a casa come ricordo della serata. Il souvenir riporta i piatti serviti durante la cena. La metà destra della pagina interna presenta righe orizzontali per la scrittura a mano dei vini da parte del sommelier.

## Utilizzo

### Interfaccia web (Streamlit)

```
streamlit run app.py
```

L'interfaccia permette di configurare fino a 5 tavoli con i rispettivi ospiti, scegliere menu e lingua, e generare tutti i PDF con un click. Anteprima e download (singolo o ZIP) integrati.

### CLI (da Excel)

1. Compilare il file Excel nella cartella `input/` (foglio "ORDINI") con i dati della serata
2. Eseguire `python scripts/genera_souvenir.py`
3. I PDF vengono generati in `output/` con nome `souvenir_DDMMYYYY_tavolo_ospite.pdf`

## Struttura del progetto

```
Souvenir Petit Bellevue/
├── assets/              # Font Bellevue.ttf + fonts/ (Bernhard Modern)
├── database/            # Fallback locale (menu_database.json)
├── input/               # File Excel per CLI
├── output/              # PDF generati
├── pages/               # Pagine Streamlit (Gestione Menu)
├── scripts/             # genera_souvenir.py, genera_guide.py
├── .streamlit/          # config.toml (tema)
├── app.py               # Interfaccia Streamlit principale
├── supabase_utils.py    # Client Supabase + CRUD
├── pdf_import.py        # Import menu da PDF via Claude Vision
├── Sfondo souvenir.pdf  # Sfondo A4 landscape (2 pagine)
├── Riga rossa.pdf       # Separatore decorativo tra piatti
└── requirements.txt
```

## Menu disponibili

I menu degustazione e i relativi piatti sono gestiti dinamicamente tramite il database (Supabase o JSON locale). La composizione dei menu si configura dalla pagina **Gestione Menu** dell'app.

| Menu | Descrizione |
|------|-------------|
| **Esprit** | Menu degustazione — composizione da database |
| **Terroir** | Menu degustazione — composizione da database |
| **Carta** | Selezione libera dal database (multiselect nell'interfaccia) |

## Formato input Excel

Il file Excel deve contenere un foglio **"ORDINI"** con le seguenti colonne:

| Colonna      | Descrizione |
|--------------|-------------|
| `data`       | Data della serata (DD/MM/YYYY) |
| `tavolo`     | Codice del tavolo (es: "1pb", "3pb") |
| `ospite`     | Nome dell'ospite |
| `lingua`     | Lingua per i testi: `it`, `fr`, `en` |
| `tipo_menu`  | `esprit`, `terroir`, `carta` |
| `piatti`     | **Solo per `carta`**: ID dei piatti separati da virgola |
| `tipo_vini`  | (ignorato — mantenuto per compatibilità) |
| `vini`       | (ignorato — mantenuto per compatibilità) |

## Layout PDF

### Pagina 1 (copertina)
- **Metà destra**: data della serata in font Bellevue, nella lingua dell'ospite
- **Metà sinistra** (retro): numero tavolo e ospite (verticale, angolo basso-sinistra)

### Pagina 2 (interno)
- **Metà sinistra**: titolo menu + piatti con separatori decorativi
- **Metà destra**: titolo "Dal regno di Bacco" + righe orizzontali per scrittura a mano dei vini (19 righe, spaziatura 8mm)
- **Basso destra**: firme Chef (Niccolò de Riu) e Sommelier (Rino Billia), tradotte per lingua

## Posizionamento piatti

- Gap naturale distribuito uniformemente, con cap a 70pt (~25mm)
- Gruppo centrato leggermente sopra il centro visivo (40/60)
- Per 6 piatti (menu degustazione): riempie l'intera area disponibile
- Per pochi piatti (carta): centrato con spaziatura elegante

## Font

- **Bellevue** — titoli e data (`assets/Bellevue.ttf`). Non include apostrofo: fallback BernhardMod per il titolo vini in inglese
- **Bernhard Modern BT** — famiglia serif (regular, italic, bold, bold italic) per testi e descrizioni (`assets/fonts/`)

## Zone proibite — decorazioni pagina 2

Le decorazioni dello sfondo sono mappate con profili per-Y pixel-esatti (`_LEFT_DECO_PROFILE`, `_RIGHT_DECO_PROFILE`): 596 valori che indicano l'estensione delle decorazioni a ogni coordinata Y. Margine di sicurezza: 5.7pt (2mm).

Il sistema anti-sovrapposizione opera in 4 fasi:
1. **Raccolta** — elementi testuali e separatori raccolti con posizioni iniziali
2. **Re-wrap iterativo** — descrizioni troppo larghe ri-splittate (max 3 iterazioni)
3. **Controllo finale ASSOLUTO** — ogni elemento verificato con estensione verticale completa (baseline ± ascent/descent). Abort se impossibile da posizionare
4. **Controllo separatori** — separatori accorciati o omessi se in zona decorazione

## Dipendenze

```
streamlit>=1.30
reportlab
pypdf
PyMuPDF
Pillow
numpy
openpyxl
pandas
supabase
anthropic
```
