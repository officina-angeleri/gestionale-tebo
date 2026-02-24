# Walkthrough: Rollback Import PDF Robecchi — Sessione 23

*Completato: 24 Febbraio 2026*

---

## Obiettivo

Rimuovere l'importazione automatica di fatture e conferme d'ordine PDF del fornitore Robecchi, ripristinando il sistema alla sola importazione massiva XML nativa.

## Interventi Effettuati (Rollback)

Il codice è stato chirurgicamente ripristinato ad uno stato precedente all'introduzione della funzionalità Robecchi PDF, mantenendo intatte le rifiniture di UI cross-reference ed estrattori SDI (aggiunte nelle sessioni 19-20).

| Componente | Dettaglio Rimozione |
|---|---|
| **Dipendenze** | Rimossa libreria `pdfplumber` da `requirements.txt`. |
| **Backend** | Rimosso `import_pdf_robecchi()` e helper sanitizzati in `data_manager.py`. Eliminato override numeri italiani e ripristinato `_parse_float`. |
| **UI** | Eliminato pulsante `📄 Sincronizza PDF Robecchi` in `main.py` e il popup riepilogativo. |

## Verifica

- L'app si avvia regolarmente.
- I pulsanti relativi all'**Import SDI (XML/P7M)** e lo svuotamento fatture rimangono funzionanti.
- L'integrità del database SQLite è preservata (lo schema non era stato alterato seicentramente).
- Compilazione eseguibile (`GestionaleTebo.exe`) generata con successo tramite `pyinstaller`.

---
*Progetto: officina-angeleri/gestionale-tebo — branch main*
