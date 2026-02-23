# Walkthrough: Import PDF Robecchi — Sessioni 21-22

*Completato: 23 Febbraio 2026*

---

## Obiettivo

Importare automaticamente fatture e conferme d'ordine PDF del fornitore Robecchi
nel database gestionale, con parser robusto, matching articoli e UI integrata.

## Feature Implementate

| Componente | Dettaglio |
|---|---|
| **Analisi PDF** | 51 file analizzati: 23 leggibili, 26 scansioni (saltate), 2 offerte (saltate) |
| **Parser backend** | `import_pdf_robecchi()` + 4 metodi helper in `data_manager.py` |
| **Parsing numeri IT** | `_parse_italian_float()`: gestisce `1.067,50` → `1067.5` |
| **Fuzzy matching** | Ricerca articolo per codice esatto, poi per descrizione (`ilike`) |
| **Deduplicazione** | Skip automatico se fattura già presente nel DB |
| **UI** | Pulsante `📄 Sincronizza PDF Robecchi` in Impostazioni con progress dialog |
| **Migrazione DB** | `ALTER TABLE fornitori ADD COLUMN categoria VARCHAR` (schema desincrono) |

## Fix Sessione 22

**Bug**: fatture con importo > 999 mostravano TOTALE € 0,00.

**Root cause**: `_parse_float("1.067,50")` → `float("1.067.50")` → *ValueError silenzioso* → `0.0`

**Fix**:
1. Nuovo `_parse_italian_float()` con logica separatore migliaia/decimale
2. Regex OC aggiornata per `\r\n` Windows
3. Fallback totale: somma righe se regex fallisce

## Risultati Test Finali

```
Importati: 22  fatture/conferme d'ordine
Righe:     70  righe articolo
Saltati:   29  (scansioni + offerte + duplicati)
Errori:    0

Top totali verificati:
  n.815  → € 2.377,50  ✅
  n.3628 → € 1.067,50  ✅
  n.1647 → € 1.478,88  ✅
```

## Come usare

1. Aprire l'app → **Impostazioni** → **Manutenzione Dati**
2. Cliccare **📄 Sincronizza PDF Robecchi**
3. Selezionare la cartella `I:\Il mio Drive\TEBO\02 Fornitori\Fatture Fornitori\Robecchi`
4. Attendere il completamento e leggere il popup riepilogo

> [!TIP]
> Il bottone è idempotente: ri-eseguirlo salta automaticamente le fatture già presenti.

> [!NOTE]
> Le 26 fatture `Robecchi Fatt...` sono PDF-immagine non estraibili e vengono
> sempre conteggiate come "saltate". Richiederebbero OCR per essere processate.

---
*Progetto: officina-angeleri/gestionale-tebo — branch main*
