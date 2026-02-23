# Import PDF Robecchi — Implementation Plan

## Obiettivo

Importare automaticamente documenti PDF del fornitore **Robecchi Articoli Tecnici Srl** dalla cartella
`I:\Il mio Drive\TEBO\02 Fornitori\Fatture Fornitori\Robecchi`.

### Contesto — Tipologie PDF trovate (51 file analizzati)

| Tipo | File | Testo estraibile | Azione |
|---|---|---|---|
| Fattura testuale | `Fattura n. XXXX del...` | ✅ 2 file | Importa come ACQUISTO |
| Conferma d'ordine | `C001578 OC XXXX...` | ✅ 21 file | Importa come ACQUISTO |
| Offerta/Preventivo | `C001578 PV XXXX...` | ✅ 2 file | **Salta** (non fattura) |
| Fattura scansionata | `Robecchi Fatt...` | ❌ 26 file | **Salta** con avviso |

---

## Proposed Changes

### Backend — `data_manager.py`

Nuovi metodi:

| Metodo | Funzione |
|---|---|
| `import_pdf_robecchi(folder, cb)` | Scansione ricorsiva `.pdf`, chiama per-file, ritorna `{'imported', 'rows', 'skipped', 'errors'}` |
| `_import_single_pdf_robecchi(path, session)` | Identifica tipo, estrae numero/data/totale, crea `Fattura` + righe, controlla duplicati |
| `_extract_rows_pdf_robecchi(text, fattura, session)` | Regex `C001578-XXXX … UM QTY PREZZO TOT`; matching esatto + fuzzy (`ilike`) |
| `_parse_robecchi_date(s)` | `DD-MM-YY` / `DD-MM-YYYY` → `date` |
| `_parse_italian_float(val)` | `1.067,50` → `1067.5` (gestisce separatore migliaia italiano) |

**Logica per tipo:**
- **FATTURA**: numero + data da TABLE 0; totale da `TOTALE FATTURA … EUR X`
- **OC**: numero + data da `Conferma d'ordine n. XXX del DD-MM-YY`; totale da `€ X.XXX,XX … INSERITO DA`
- **Fallback totale**: se 0 dopo regex → somma `totale_riga` delle righe create
- **Deduplicazione**: skip se `Fattura(tipo=ACQUISTO, numero=X, fornitore_codice=ROBECCHI)` esiste
- **Auto-creazione fornitore**: inserisce ROBECCHI con dati fissi se assente

**Costanti fornitore:**
```python
ROBECCHI_CODICE        = 'ROBECCHI'
ROBECCHI_PIVA          = '00843220161'
ROBECCHI_DENOMINAZIONE = 'Robecchi Articoli Tecnici Srl'
```

### Frontend — `main.py`

- Metodo `import_pdf_robecchi_ui()`:
  - `QFileDialog.getExistingDirectory` (default: ultima cartella o path standard)
  - `QProgressDialog` modale, aggiornato per-file
  - Popup riepilogo con ✅ / 📦 / ⏭ / ❌
  - Salva cartella scelta in `column_prefs.json['robecchi_pdf_folder']`
- Pulsante `📄 Sincronizza PDF Robecchi` → Impostazioni → Manutenzione Dati

### `requirements.txt`
Aggiunto: `pdfplumber`

### Migrazione DB
```sql
ALTER TABLE fornitori ADD COLUMN categoria VARCHAR;
```

---

## Verification Plan

```
python test_pdf_robecchi.py
# Atteso: imported≥20, errors=0
```

**Risultato ottenuto:**
```
Importati: 22, Righe: 70, Saltati: 29, Errori: 0
n.815  totale=2377.50 ✅
n.3628 totale=1067.50 ✅
```
