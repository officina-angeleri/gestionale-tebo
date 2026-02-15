# Gestionale Tebo — Storia dello Sviluppo

> Documento centrale di tracciamento per il progetto **Gestionale Tebo**.
> Aggiornato: 14 Febbraio 2026

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

---
*Aggiornato progressivamente durante lo sviluppo.*
