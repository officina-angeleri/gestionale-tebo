# Gestionale Tebo — Storia dello Sviluppo

> Documento centrale di tracciamento per il progetto **Gestionale Tebo**.
> Aggiornato: 23 Febbraio 2026 — **Versione 2.0-dev**

---

## 1. Panoramica del Progetto

**Gestionale Tebo** è un'applicazione desktop per la gestione di clienti, fornitori, articoli e fatture dell'azienda Tebo. I dati vengono importati da file Excel esistenti.

| Elemento | Dettaglio |
|---|---|
| **Linguaggio** | Python 3 |
| **GUI Framework** | PySide6 (Qt) |
| **Database** | SQLite (locale, `tebo.db`) |
| **ORM** | SQLAlchemy |
| **Importazione dati** | Pandas (da file `.xls`) |
| **Repository** | `officina-angeleri/gestionale-tebo` (GitHub) |
| **Branch principale** | `main` |

---

## 2. Struttura del Progetto

```
gestionale-tebo/
├── main.py              # Entry point, GUI principale, dialoghi
├── database.py          # Modelli SQLAlchemy (Cliente, Fornitore, Articolo, Fattura, RigaFattura)
├── data_manager.py      # Logica di importazione da Excel
├── init_db.py           # Script per inizializzare/ricreare il database
├── requirements.txt     # Dipendenze Python
├── column_prefs.json    # Preferenze colonne utente (generato a runtime)
├── .gitignore           # Esclude *.db, __pycache__, venv, ecc.
├── docs/
│   ├── storia_sviluppo.md   # Questo file
│   └── ai_history/          # Artefatti di sviluppo AI
│       ├── task.md
│       ├── implementation_plan.md
│       └── walkthrough.md
├── gui/
│   └── main_window.py   # (legacy, non più usato — la GUI è in main.py)
└── *.xls                # File Excel sorgente (non versionati)
```

---

## 3. File Excel Sorgente

| File | Contenuto | Righe (circa) |
|---|---|---|
| `TEBO_ELENCO_CLIENTI.xls` | Anagrafica clienti (codice, ragione sociale, indirizzo, telefono, email…) | ~1430 |
| `TEBO_ELENCO_FORNITORI.xls` | Anagrafica fornitori | ~50 |
| `TEBO_ELENCO_ARTICOLI.xls` | Catalogo articoli (codice, descrizione, prezzo, UM) | ~15.000 |
| `TEBO_ELENCO_DETTAGLIO_RIGHE_VENDITA.xls` | Righe di dettaglio fatture (non singole vendite, ma righe raggruppabili per fattura) | ~4.100 |

> **Nota**: i file `.xls` non vengono versionati su GitHub (presenti in `.gitignore`). Devono essere presenti nella cartella principale per l'importazione.

---

## 4. Schema Database

### Tabella `clienti`
`id` (PK auto), `codice` (PK), `codice_alternativo`, `ragione_sociale` (Descrizione), `indirizzo`, `cap`, `localita` (Città), `provincia` (PR), `nazione`, `partita_iva` (P. IVA), `codice_fiscale` (C. fiscale), `telefono`, `email` (E-mail), `cellulare`, `telefono2`, `pagamento` (Codice Pagamento), `descrizione_pagamento`, `banca`, `filiale`, `abi`, `cin`, `conto_corrente` (c/c), `iban`, `bic`, `internet`, `commento`, `riferimento`, `zona`, `area`, `categoria`, `statistico`, `agente`, `listino`

### Tabella `fornitori`
`codice` (PK), `ragione_sociale`, `indirizzo`, `cap`, `localita`, `provincia`, `nazione`, `telefono`, `fax`, `email`, `piva`, `codice_fiscale`

### Tabella `articoli`
`codice` (PK), `descrizione`, `prezzo`, `um`

### Tabella `fatture`
`id` (PK auto), `numero` (Nr Fat), `data` (Data Fat), `cliente_codice` (testo, non FK), `cliente_denominazione` (nome cliente dal file Excel), `totale`, `causale`

### Tabella `righe_fattura`
`id` (PK auto), `fattura_id` (FK → fatture.id), `numero_ddt`, `data_ddt`, `articolo_codice`, `descrizione`, `quantita`, `prezzo_unitario`, `totale_riga`

---

## 5. Funzionalità Implementate

### v1 — Setup iniziale (13 Feb 2026)
- [x] Struttura progetto e repository Git
- [x] Modelli database SQLAlchemy (Clienti, Fornitori, Articoli)
- [x] Import dati da Excel (Pandas)
- [x] GUI base PySide6 con sidebar e navigazione a tab
- [x] Tabelle dati (Clienti, Fornitori, Articoli)
- [x] Dashboard con statistiche rapide
- [x] Push iniziale su GitHub

### v2 — Fatture (14 Feb 2026)
- [x] Ristrutturazione "Vendite" → "Fatture"
- [x] Raggruppamento righe Excel per numero fattura e data
- [x] Modello `Fattura` + `RigaFattura` con relazione 1:N
- [x] Nome cliente memorizzato come testo (campo `cliente_denominazione`)
- [x] Rimozione limite 500 righe — caricamento completo
- [x] Vista principale: elenco fatture con ID, Numero, Data, Codice Cliente, Cliente, Causale, Totale
- [x] Dettaglio fattura (doppio clic): dialog con dati testata + tabella righe
- [x] Ordinamento colonne (clic su intestazione: crescente/decrescente)
- [x] Ordinamento intelligente: numerico per €/numeri, cronologico per date, alfabetico per testo
- [x] Configurazione colonne visibili (pulsante ⚙ per ogni tabella)
- [x] Preferenze colonne persistenti (`column_prefs.json`)
- [x] Ridimensionamento manuale colonne nel dettaglio fattura (con salvataggio larghezze)

### v3 — Clienti (14 Feb 2026)
- [x] Espansione modello `Cliente` per includere tutti i 31 campi presenti in Excel
- [x] Aggiornamento logica import per mappare tutte le colonne
- [x] Implementazione `ClientDetailDialog` con visualizzazione a gruppi di tutti i campi
- [x] Abilitazione configurazione e persistenza colonne per la tabella Clienti
- [x] Re-importazione massiva di 1400+ clienti con i nuovi dati completi

---

## 6. Decisioni Progettuali Chiave

| # | Decisione | Motivazione |
|---|---|---|
| 1 | **SQLite locale** | Applicazione single-user, dati sincronizzati via Synology NAS |
| 2 | **PySide6** (non Tkinter) | Più moderno, stessa scelta del progetto Gestionale Karate |
| 3 | **SQLAlchemy ORM** | Astrazione dal DB, facilità di modifica schema |
| 4 | **Cliente come testo in fattura** | I codici cliente nelle righe vendita non sempre corrispondono all'anagrafica. Salviamo il nome testuale dall'Excel |
| 5 | **Niente FK cliente → fattura** | Evita errori di integrità referenziale durante l'importazione con dati incompleti |
| 6 | **SortableItem custom** | Qt ordina tutto come testo per default. Sottoclasse `QTableWidgetItem` con `__lt__` che confronta valori raw |
| 7 | **Preferenze colonne in JSON** | Semplice, leggibile, versionabile. File `column_prefs.json` |

---

## 7. Problemi Risolti

| # | Problema | Soluzione |
|---|---|---|
| 1 | Percorsi file non trovati cross-directory | Usato `os.path.dirname(os.path.abspath(__file__))` |
| 2 | Limite 500 righe nelle tabelle | Rimosso `limit = 500` dalla query |
| 3 | Nomi clienti mostrati come codici | Aggiunto campo `cliente_denominazione` importato dall'Excel |
| 4 | Errore `'RigaFattura' has no attribute 'um'` | Accesso sicuro a `r.articolo.um` |
| 5 | `session.query().get()` deprecato | Sostituito con `session.get()` |
| 6 | Ordinamento € numerico | Implementato `SortableItem` con raw value |
| 7 | Push GitHub fallito (403) | Aggiornato remote URL con username |
| 8 | Apertura fattura fallisce con ID nascosto | Cerca l'ID nel `UserRole` di tutte le colonne |

---

## 8. Sintesi Chat di Sviluppo

### Sessione 1 — 13 Febbraio 2026
**Obiettivo**: Setup iniziale del progetto.
- Analisi Excel, modelli DB, GUI sidebar, import dati.

### Sessione 2 — 14 Febbraio 2026 (mattina)
**Obiettivo**: Ristrutturazione Vendite → Fatture.
- Raggruppamento per fattura, dettaglio, ordinamento, configurazione colonne.

### Sessione 3 — 14 Febbraio 2026 (pomeriggio)
**Obiettivo**: Potenziamento scheda Clienti.
- Espansione modello `Cliente` (31 campi), import completo, `ClientDetailDialog` di gruppo, configurazione colonne.
- Perfezionamento importazione: rimozione segnaposto `"nan"` (gestione valori `NaN` come stringhe vuote).
- Fix mappatura colonne Excel con spazi (Indirizzo, P. IVA, Area, Listino) per garantire l'importazione di via e numero civico.
- Rebuild database e ri-importazione completa.

### Sessione 4 — 14 Febbraio 2026 (fine mattina)
**Obiettivo**: Potenziamento scheda Fornitori.
- Espansione modello `Fornitore` (25 campi): Indirizzo Esteso, Nazione, Partita IVA Intra, Fax, ecc.
- Aggiornamento logica import per mappare tutte le colonne del file `TEBO_ELENCO_FORNITORI.xls`.
- Implementazione `SupplierDetailDialog` con visualizzazione a gruppi (Dati Generali, Indirizzo, Contatti, Pagamento, Altro).
- Abilitazione configurazione e persistenza colonne per la tabella Fornitori.
- Rebuild DB e re-import completo.

### Sessione 5 — 14 Febbraio 2026 (fine mattina)
**Obiettivo**: Navigazione bidirezionale Fatture <-> Clienti.
- Aggiunta colonna "Azioni" in tabella Fatture per aprire direttamente il dettaglio del cliente.
- Aggiunta colonna "Azioni" in tabella Clienti per aprire l'elenco filtrato delle fatture del cliente.
- Implementazione `ClientInvoicesDialog` per gestire la visualizzazione filtrata.
- Aggiunta tasti di salto rapido ("Vedi Cliente" / "Vedi Fatture") all'interno dei dialoghi di dettaglio.

### Sessione 6 — 14 Febbraio 2026 (pasti)
**Obiettivo**: Branding e Impostazioni.
- Implementata **Top Bar** con loghi Angeleri e Tebo (PNG).
- Aggiunta scheda **Impostazioni** per cambio tema (**Chiaro/Scuro**) e manutenzione dati.
- Spostamento tasto **Importa Excel** in Impostazioni per maggiore sicurezza.
- Persistenza del tema scelto tra le sessioni.

### Sessione 7.1 — 14 Febbraio 2026 (mezzogiorno)
**Obiettivo**: Ricerca Fatture Robusta (Fix Bidirezionale).
- Potenziata `open_invoices_by_client` per gestire codici cliente incoerenti (es: "303" vs "00303") nelle fatture.
- Implementato l'uso di `sqlalchemy.or_` per cercare simultaneamente per codice (in varie forme) e per ragione sociale.
- Aggiornati i richiami dalla tabella clienti e dalla scheda dettaglio cliente.

### Sessione 8 — 14 Febbraio 2026 (pomeriggio)
**Obiettivo**: Gestione Finestre e Prevenzione Loop.
- Implementato un registro centrale delle finestre aperte (`detail_windows`) in `MainWindow`.
- Sostituite le finestre modali con finestre gestite: se una scheda è già aperta, viene portata in primo piano invece di crearne un duplicato.
- Eliminato il rischio di loop infiniti nella navigazione ricorsiva tra Clienti e Fatture.

### Sessione 9 — 14 Febbraio 2026 (pomeriggio)
**Obiettivo**: Gestione Dinamica del Database.
- Implementata la visualizzazione del percorso database attivo nella Dashboard.
- Aggiunta la possibilità di cambiare database tramite `QFileDialog` nella scheda Impostazioni.
- Implementata la riconnessione dinamica e la persistenza del percorso scelto in `column_prefs.json`.
- Aggiunta validazione per garantire che il file selezionato sia un database SQLite valido.

---

### Session 10 — 14 Febbraio 2026 (pomeriggio)
**Obiettivo**: Articoli e Filtri Avanzati.
- Implementata scheda dettaglio per gli **Articoli** (`ArticleDetailDialog`) con pesi e prezzi.
- Aggiunta colonna "Azioni" alla tabella Articoli con tasto "Vedi".
- Implementati **Filtri Avanzati**:
    - **Articoli**: Filtro per intervallo di prezzo (Min/Max).
    - **Fatture**: Filtro per intervallo di date (Dal/Al).
- **Altro**: Rimosso il limite di 500 righe nelle tabelle (ora mostra tutti i ~15.000 articoli).
- Fix ambiente: installazione dipendenze `PySide6` nel venv.

---

### Session 11 — 14 Febbraio 2026 (pomeriggio, cont.)
**Obiettivo**: Integrazione Azioni Rapide e Riepiloghi.
- **Scheda Fatture Cliente**: Aggiunto footer con conteggio totale fatture e somma importi.
- **Schede Dettaglio (Clienti/Fornitori)**:
    - Implementati pulsanti azione con **icone vettoriali SVG**.
    - **Gestione Email Dinamica**: La `MailSelectorDialog` ora scansiona il rgistro di Windows per trovare app come Thunderbird e Outlook.
    - **UI/UX Refinement**: Ottimizzata la leggibilità con caratteri più grandi, contrasti elevati e raggruppamento logico delle opzioni. Risolto il bug del tasto "Annulla" che appariva schiacciato aumentando l'altezza minima della finestra e dei componenti.
- **Tecnico**: Utilizzo di `winreg` per il rilevamento app e CSS personalizzato per l'accessibilità.

---

### Session 12 — 15 Febbraio 2026
**Obiettivo**: Perfezionamento UI e Ordinamento.
- **Ricerca Articolo**: Resa ridimensionabile la colonna "Descrizione Articolo" e implementata la persistenza delle larghezze delle colonne (`article_search_widths`).
- **Ordinamento Cronologico**: Corretto l'ordinamento della colonna **Data** in tutte le viste (Fatture, Ricerca Articoli, ecc.). Ora l'ordinamento avviene su oggetti `date` reali invece che su stringhe, garantendo la corretta sequenza temporale.
- **Interfaccia**: Uniformato l'uso di `make_item` per tutte le celle per supportare l'ordinamento intelligente.

---

### Session 13 — 15 Febbraio 2026
**Obiettivo**: Affinamento Ricerca Articoli.
- **Selezione Campi**: Aggiunte checkbox nella `ArticleSearchDialog` per permettere all'utente di scegliere se cercare per "Codice articolo", "Descrizione articolo" o entrambi.
- **Logica di Ricerca**: Aggiornato il metodo `perform_search` per costruire dinamicamente i filtri SQL (OR logico tra i campi selezionati) in base alle preferenze dell'utente.
- **Default**: Se nessun campo è selezionato, la ricerca avviene automaticamente su entrambi per garantire risultati immediati.

### Session 14 — 15 Febbraio 2026
**Obiettivo**: Miglioramento Interazione Ricerca.
- **Doppio Clic**: Abilitato l'apertura del dettaglio fattura tramite doppio clic su qualsiasi riga dei risultati della ricerca articoli, allineando il comportamento alle altre tabelle dell'applicazione.
- **UX**: Il pulsante "Dettaglio Fattura" rimane disponibile, ma l'azione rapida ora è supportata nativamente.
- **Rinominazione**: La scheda "Fatture" è stata rinominata in "Fatture Clienti" per maggiore chiarezza.
- **Layout**: Risolto un problema di troncamento del titolo nelle intestazioni delle tabelle rimuovendo la larghezza fissa.

### Session 15 — 15 Febbraio 2026
**Obiettivo**: Ricerca Incrementale.
- **Funzionalità**: Implementata la modalità "Ricerca Incrementale" nella finestra di ricerca articoli.
- **Logica**:
    - **OFF (Default)**: Ogni ricerca riparte da zero su tutto il database.
    - **ON**: Le nuove ricerche filtrano i risultati correnti, permettendo di affinare la selezione (es: "tubo" -> poi "pvc" -> trovi tubi in pvc).
- **UI**: Aggiunto checkbox di attivazione e un'etichetta di stato che indica chiaramente la modalità corrente (Nuova ricerca vs Incrementale).

---

## 9. Prompt Principali Usati

> "Rinomina la sezione Vendite in Fatture... raggruppabili per fattura... doppio clic visualizza dettaglio."

> "Importa sempre il nome del cliente così come è presente nel file... non forzare FK."

> "Permetti all'utente di scegliere quali colonne visualizzare... salva e ripristina."

> "Nella scheda dettaglio di ogni cliente devono essere presenti tutti i campi disponibili... vista completa e fedele."

> "Rendi robusta la ricerca bidirezionale gestendo zeri iniziali e fallback sul nome del cliente."

> "Impedisci loop infiniti di finestre usando un registro centrale per portare in primo piano le schede già aperte."

> "Aggiungi la possibilità di cambiare il percorso del database dalle impostazioni e mostralo nella dashboard."

---

## 10. Prossimi Passi

- [x] Migliorare la sezione **Clienti** (dettaglio completo, configurazione colonne)
- [x] Migliorare la sezione **Fornitori** (dettaglio completo, configurazione colonne)
- [x] Implementare **incrocio strutturato** fatture-clienti (navigazione bidirezionale)
- [ ] Migliorare la sezione **Articoli** (dettaglio, modifica, ricerca avanzata)
- [ ] Aggiungere vista dettaglio per singolo Articolo
- [ ] Aggiungere **filtri avanzati** (data, cliente, importo)
- [x] Documentazione strutturata dello sviluppo (`storia_sviluppo.md`)
- [x] Implementare backend **Fatture Fornitori** (parser SDI, import batch)
- [x] Implementare GUI **Fatture Fornitori** (scheda sidebar, tabella, dialogo dettaglio)
- [x] Fix robustezza parsing SDI (multi-livello, Base64, regex fallback)
- [x] Funzione "Svuota Fatture Fornitori"

---

### Session 16 — 18 Febbraio 2026
**Obiettivo**: Analisi fatture fornitori e backend Fatture Acquisto.
- **Analisi file SDI**: esaminate 2 fatture elettroniche SDI (formato FPR12, firmate CAdES `.p7m`) di UTENSILERLA MONZESE s.r.l. Tutti i campi richiesti presenti (numero, data, fornitore, righe con codice/descrizione/qtà/prezzo/IVA/sconti).
- **Schema DB**: aggiornato `Fattura` con campi `tipo` (VENDITA/ACQUISTO), `fornitore_codice`, `fornitore_denominazione`.
- **Backend SDI** in `data_manager.py`:
  - `extract_xml_from_p7m()` — estrazione payload XML da CAdES con fallback multipli
  - `parse_fattura_xml()` — parsing XML SDI con auto-rilevamento encoding e regex fallback
  - `import_fattura_acquisto_sdi()` — import singola fattura, gestione duplicati, auto-creazione fornitore
  - `batch_import_from_folders()` — scansione ricorsiva cartelle, deduplicazione `.xml > .p7m`, progress callback
- **Cartella test**: aggiunta `test_batch_sdi/` con sottocartelle `sub1/` (`.p7m`) e `sub2/` (`.xml` + `.p7m`) per test import batch.
- **Push** su GitHub (`officina-angeleri/gestionale-tebo`).

### Session 17 — 19 Febbraio 2026
**Obiettivo**: Fix migrazione database — colonne mancanti.
- **Problema**: l'app usava il DB sul NAS (`//angeleri_new/TEBO/tebo.db`). Le nuove colonne (`tipo`, `fornitore_codice`, `fornitore_denominazione`) erano presenti nel modello SQLAlchemy ma non nel DB fisico → errore `no such column: fatture.tipo`.
- **Soluzione**: creato `migrate_db.py` — script di migrazione che legge automaticamente il percorso DB da `column_prefs.json` ed esegue `ALTER TABLE fatture ADD COLUMN` per le colonne mancanti.
- Migrazione eseguita con successo su entrambi i DB (locale e NAS).

### Session 18 — 19 Febbraio 2026
**Obiettivo**: Implementazione Filtro Avanzato Esclusione Servizi in Fatture Fornitori.
- **`database.py`**: aggiunto campo `categoria` (default `'CORE'`) al modello `Fornitore` per distinguere fornitori core da servizi/utenze/GDO.
- **`migrate_db.py`**: refactoring completo — ora supporta più tabelle con una funzione `migrate_table()`. Aggiunta migrazione per `fornitori.categoria`.
- **`main.py`**:
  - **Costante `FORNITORI_SERVIZIO_DEFAULT`**: lista predefinita di fornitori da escludere (TIM, ENEL, ENI, A2A, GDO, telecom, ecc.).
  - **GUI Fatture Fornitori**: aggiunti filtri data (Dal/Al) e toggle **"⚡ Escludi Servizi"** (checkable, stato persistito in `column_prefs.json`).
  - **Barra totali**: sotto la top-bar mostra in tempo reale *"Visibili: N fatture — € X.XX"* e *"Vista completa: N fatture — € X.XX"* per verifica coerenza con l'importazione massiva.
  - **`filter_table`**: esteso per `fatture_fornitori` — filtra per data, testo, e logica esclusione per nome fornitore (confronto parziale, case-insensitive). Aggiorna le label dei totali ad ogni applicazione del filtro.
  - **Impostazioni**: aggiunta sezione "Filtro Esclusione Servizi" con editor testuale della lista (un nome per riga), pulsante Salva e pulsante Ripristina Predefiniti.
- Migrazione DB eseguita su NAS (`//angeleri_new/TEBO/tebo.db`).

### Session 21 — 18 Febbraio 2026
**Obiettivo**: Fix Robustezza Parsing SDI/P7M — Parsing Multi-Livello.
- **Problema**: Alcuni file `.p7m` causavano errori `junk after document element` o `invalid token` durante l'import.
- **Strategia multi-livello** in `extract_xml_from_p7m()` e `parse_fattura_xml()`:
  - **Livello 1**: estrazione chirurgica bidirezionale (da `<?xml` a `</FatturaElettronica>`).
  - **Livello 2 (Line-Based Fallback)**: se il parsing fallisce, lettura riga per riga con focus sulla riga contenente l'XML (es. 4ª riga).
  - **Livello 3 (Radical Cleaner)**: pulizia di tutti i caratteri non stampabili rispettando l'integrità multi-byte UTF-8; sostituzione di byte sospetti prima del parsing.
  - **Livello 4 (Regex Fallback — Ultima Spiaggia)**: se l'XML è strutturalmente irrecuperabile per ElementTree, estrazione di numero, data e fornitore tramite regex per salvare almeno i dati di testata.
- **Fix righe senza codice articolo**: le `DettaglioLinee` prive di `CodiceArticolo` vengono comunque importate come righe descrittive invece di essere scartate.
- **Support Base64**: gestione del payload XML codificato in Base64 all'interno dei file `.p7m` binari.

### Session 22 — 18 Febbraio 2026
**Obiettivo**: Funzione "Svuota Fatture Fornitori".
- **Backend** (`data_manager.py`): aggiunto metodo `delete_all_fatture_acquisto()` che elimina in cascata tutte le `Fattura` di tipo `ACQUISTO` e le relative `RigaFattura`.
- **GUI** (`main.py`): aggiunto pulsante "🗑 Svuota Fatture Fornitori" in Impostazioni con `QMessageBox` di conferma a doppio step.
- **Push** su GitHub (`officina-angeleri/gestionale-tebo`, tag `v2.0-dev`).

---
*Aggiornato progressivamente durante lo sviluppo.*

---

## 🏁 Rilascio Versione 1.0 — 19 Febbraio 2026

### Funzionalità incluse nella v1.0

| Sezione | Funzionalità |
|---|---|
| **Dashboard** | Statistiche riassuntive (clienti, fornitori, articoli, fatture) |
| **Clienti** | Tabella con ricerca full-text, ordinamento colonne, visibilità colonne configurabile, dettaglio cliente |
| **Fornitori** | Tabella con ricerca, dettaglio fornitore, campo `categoria` (CORE/SERVIZIO) |
| **Articoli** | Tabella con filtro prezzo min/max, ricerca, dettaglio articolo |
| **Fatture Clienti** | Tabella con filtro data, ricerca articolo, dettaglio fattura con righe, apertura PDF |
| **Fatture Fornitori** | Import SDI (`.p7m`/`.xml`), import batch da cartella, filtri data, **toggle "Escludi Servizi"**, barra totali visibili/completi, dettaglio fattura |
| **Impostazioni** | Percorso DB configurabile (locale/NAS), import Excel, lista esclusione servizi configurabile |
| **Generali** | Wildcard search (`%`), ordinamento cronologico date, preferenze colonne e ordine persistiti per sessione |

### Struttura progetto al rilascio v1.0

```
gestionale-tebo/
├── main.py                  # GUI principale (2400+ righe)
├── database.py              # Modelli SQLAlchemy (v1.0 schema)
├── data_manager.py          # Import Excel + SDI, parsing fatture elettroniche
├── migrate_db.py            # Migrazione DB incrementale (multi-tabella)
├── init_db.py               # Inizializzazione schema DB
├── GestionaleTebo.spec      # Build PyInstaller
├── requirements.txt         # Dipendenze Python
├── column_prefs.json        # Preferenze utente (runtime, non versionato)
├── docs/
│   └── storia_sviluppo.md   # Questo file
├── gui/                     # Moduli GUI legacy (non usati)
├── test_batch_sdi/          # File SDI di test (sub1/, sub2/)
└── *.xls / *.png            # Asset e dati sorgente (non versionati)
```

### Schema DB v1.0

| Tabella | Colonne chiave | Note |
|---|---|---|
| `clienti` | id, codice, ragione_sociale, … (25 campi) | Import da Excel CLIENTI |
| `fornitori` | id, codice, ragione_sociale, **categoria**, … | `categoria`: CORE/SERVIZIO |
| `articoli` | id, codice, descrizione, prezzo, um, peso | Import da Excel ARTICOLI |
| `fatture` | id, **tipo**, numero, data, cliente/fornitore, totale, causale | tipo: VENDITA/ACQUISTO |
| `righe_fattura` | id, fattura_id, articolo_codice, descrizione, quantita, prezzo | FK → fatture, articoli |

### Build exe

```bash
# Installa dipendenze
pip install -r requirements.txt pyinstaller

# Compila
pyinstaller GestionaleTebo.spec

# Output: dist/GestionaleTebo/GestionaleTebo.exe
```

### Tag git

```bash
git tag -a v1.0 -m "Gestionale Tebo versione 1.0"
git push origin v1.0
```

---
*Aggiornato: 19 Febbraio 2026 — versione 1.0 stabile. Sviluppo v2.0 attivo dal 19 Febbraio 2026.*

---

## 🚀 Versione 2.0 — Sviluppi Post-1.0

### Session 19 — 19 Febbraio 2026
**Feature**: Cross-Reference Articoli tra Fatture e Anagrafica.
- **Nuova classe `CrossReferenceDialog`** in `main.py`:
  - Aperta dal pulsante `🔍` in ogni riga del dettaglio fattura (sia Clienti che Fornitori).
  - **Tab 🛒 Acquisti**: tutte le righe di fatture fornitore con quel codice articolo — Data, Fornitore, N° Fatt., Qtà, Prezzo Acquisto, Tot. Riga. Sommario quantità e valore totale.
  - **Tab 💰 Vendite**: tutte le righe di fatture cliente con quel codice — Data, Cliente, N° Fatt., Qtà, Prezzo Vendita, Tot. Riga. Sommario quantità e valore totale.
  - **Tab 📦 Anagrafica**: dati tecnici articolo (codice, descrizione, UM, prezzo listino, pesi). Se l'articolo **non esiste** in anagrafica → form "Crea in Anagrafica" pre-popolato con i dati della riga fattura corrente.
- **Modifica `InvoiceDetailDialog`**: aggiunta 7ª colonna `🔍` nella tabella righe. Pulsante disabilitato per righe senza `articolo_codice`.
- Nessuna modifica al DB — usa `RigaFattura.articolo_codice` come chiave di ricerca.
- **Fix**: aggiunto `QTabWidget` e `QTextEdit` agli import `PySide6.QtWidgets` (mancavano).

### Session 20 — 19 Febbraio 2026
**Feature**: Miglioramento Scheda Articolo, UdM obbligatorio, Cross-Reference inverso.
- **`ArticleDetailDialog`** riscritta con layout a 3 tab:
  - **📋 Dati**: codice, descrizione, UM, prezzo listino, pesi — etichette teal scuro, valori quasi-neri, alta leggibilità.
  - **🛒 Acquisti (n)**: tutte le righe di fatture fornitore con quel codice — Data, Fornitore, N° Fatt., Qtà, Prezzo. Totale righe e valore in footer.
  - **💰 Vendite (n)**: tutte le righe di fatture cliente — Data, Cliente, N° Fatt., Qtà, Prezzo.
- **`CrossReferenceDialog` — Tab Anagrafica**: contrasto elevato (testo scuro su sfondo chiaro); campi Codice/Descrizione/Prezzo editabili anche se articolo trovato; **UdM (`QComboBox`)** obbligatoria con opzioni predefinite `nr / mt / kg / lt / conf` — salvataggio bloccato se vuota.
- **Fix colori**: corretti `VALUE_SS` e `KEY_SS` da colori chiari (`#e0e0e0`, `#80cbc4`) a scuri (`#212121`, `#00695c`) per garantire leggibilità su sfondo di sistema bianco.

### Session 21 — 23 Febbraio 2026
**Feature**: Import automatico PDF Robecchi (fatture e conferme d'ordine).

#### Analisi PDF
Scansionati 51 PDF in `I:\...\Robecchi`:
- **26 scansioni** (`Robecchi Fatt...`): PDF-immagine, nessun testo → saltati con avviso
- **21 Conferme d'Ordine** (`C001578 OC...`): testo selezionabile ✅
- **2 Fatture testuali** (`Fattura n. XXXX...`): ✅
- **2 Offerte** (`C001578 PV...`): leggibili ma non fatture → saltate

#### Backend — `data_manager.py`
Nuovi metodi aggiunti:

| Metodo | Funzione |
|---|---|
| `import_pdf_robecchi(folder, cb)` | Entry point: scansione ricorsiva, ritorna `{'imported', 'rows', 'skipped', 'errors'}` |
| `_import_single_pdf_robecchi(path, session)` | Parser: identifica tipo documento, estrae numero/data/totale con regex, crea `Fattura` + righe, controlla duplicati |
| `_extract_rows_pdf_robecchi(text, fattura, session)` | Regex `C001578-XXXX DESCRIZIONE UM QTY PREZZO TOT`; matching esatto codice articolo DB + fuzzy fallback su descrizione (`ilike`) |
| `_parse_robecchi_date(s)` | Converte `DD-MM-YY` o `DD-MM-YYYY` → `date` |
| `_parse_italian_float(val)` | Converte numeri formato italiano (`1.067,50` → `1067.5`), distingue separatore migliaia da decimale |

**Logica importazione per tipo documento:**
- **FATTURA**: numero e data da TABLE 0 (celle `N° DOCUMENTO` / `DATA DOC.`), totale da regex `TOTALE FATTURA ... EUR X`
- **OC Conferma d'ordine**: numero e data da regex `Conferma d'ordine n. XXX del DD-MM-YY`, totale da regex `€ X.XXX,XX` prima di `INSERITO DA`
- **Fallback totale**: se totale = 0 dopo estrazione, viene calcolato come somma delle `RigaFattura.totale_riga`
- **Deduplicazione**: skip se `Fattura` con stesso `numero` + `fornitore_codice='ROBECCHI'` + `tipo='ACQUISTO'` già presente
- **Auto-creazione fornitore**: se `ROBECCHI` non è nel DB, viene creato con dati fissi (P.IVA, sede, email)

#### Frontend — `main.py`
- **`import_pdf_robecchi_ui()`**: handler con `QFileDialog`, `QProgressDialog` modale per-file, popup riepilogo con emoji
- **Pulsante** `📄 Sincronizza PDF Robecchi` nella sezione **Manutenzione Dati** → Impostazioni (affianco a SDI)
- Ultima cartella usata salvata in `column_prefs.json` (`robecchi_pdf_folder`)
- Spostati anche i pulsanti SDI (file + cartella) dentro lo stesso gruppo

#### Migrazione DB
Il DB SQLite era privo della colonna `fornitori.categoria` (modello aggiornato ma DB non migrato):
```sql
ALTER TABLE fornitori ADD COLUMN categoria VARCHAR;
```

#### `requirements.txt`
Aggiunta dipendenza: `pdfplumber`

#### Risultati test
```
Importati: 22  fatture/conferme d'ordine
Righe:     70  righe articolo (con codice C001578-XXXX)
Saltati:   29  (26 scansioni + 2 offerte + 1 duplicato)
Errori:    0
```

### Session 22 — 23 Febbraio 2026
**Fix**: Totali fatture Robecchi mostravano € 0,00.

**Causa**: `_parse_float` generico trasformava `1.067,50` (formato IT) in `1.067.50` (float non valido) → silenziosamente `0.0`.

**Fix in `data_manager.py`**:
1. Nuovo metodo `_parse_italian_float()`: se contiene sia `.` che `,` → rimuove il punto (migliaia) e converte virgola in punto decimale
2. Regex totale OC migliorata per gestire `\r\n` (Windows) tra importo e `INSERITO DA`
3. Fallback totale: se ancora 0 dopo estrazione regex, sommato dalle righe importate
4. Tutti i metodi `_extract_rows_pdf_robecchi` / estrazione totale ora usano `_parse_italian_float`

**Risultati dopo fix e re-import**:
```
n.815  → € 2.377,50  (era € 0,00)
n.3628 → € 1.067,50  (era € 0,00)
... tutti i totali corretti
```

