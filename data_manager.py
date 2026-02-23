import pandas as pd
from sqlalchemy.orm import Session
from database import DatabaseManager, Cliente, Fornitore, Articolo, Fattura, RigaFattura
from datetime import datetime
import os
import re
import xml.etree.ElementTree as ET

class DataManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def import_all(self):
        session = self.db_manager.get_session()
        try:
            # Resolve paths relative to this script file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            self.import_fornitori(session, os.path.join(base_dir, "TEBO_ELENCO_FORNITORI.xls"))
            self.import_clienti(session, os.path.join(base_dir, "TEBO_ELENCO_CLIENTI.xls"))
            self.import_articoli(session, os.path.join(base_dir, "TEBO_ELENCO_ARTICOLI.xls"))
            self.import_vendite(session, os.path.join(base_dir, "TEBO_ELENCO_DETTAGLIO_RIGHE_VENDITA.xls"))
            session.commit()
            print("Importazione completata con successo.")
        except Exception as e:
            session.rollback()
            print(f"Errore durante l'importazione: {e}")
            raise
        finally:
            session.close()

    def _clean(self, val):
        """Convert NaN/None/inf to empty string, otherwise return as string stripped."""
        if pd.isna(val) or val is None:
            return ""
        s = str(val).strip()
        if s.lower() in ["nan", "none", "inf", "-inf"]:
            return ""
        # Handle decimal points in what should be integers (like Cap or Codice)
        if s.endswith(".0"):
            s = s[:-2]
        return s

    def _read_excel(self, filename):
        if not os.path.exists(filename):
            print(f"File non trovato: {filename}")
            return pd.DataFrame()
        return pd.read_excel(filename)

    def import_fornitori(self, session: Session, filename):
        df = self._read_excel(filename)
        print(f"Importazione Fornitori da {filename} ({len(df)} righe)...")
        for _, row in df.iterrows():
            codice = self._clean(row.get('Codice', ''))
            
            existing = session.query(Fornitore).filter_by(codice=codice).first()
            if not existing:
                fornitore = Fornitore(
                    codice=codice,
                    ragione_sociale=self._clean(row.get('Ragione sociale', '')),
                    indirizzo_esteso=self._clean(row.get('Indirizzo Esteso', '')),
                    indirizzo=self._clean(row.get('Indirizzo', '')),
                    cap=self._clean(row.get('CAP', '')),
                    localita=self._clean(row.get('Città', '')),
                    provincia=self._clean(row.get('PR', '')),
                    nazione=self._clean(row.get('Codice nazione', '')),
                    codice_fiscale=self._clean(row.get('C. fisc.', '')),
                    partita_iva=self._clean(row.get('P. IVA', '')),
                    partita_iva_intra=self._clean(row.get('IVA Intra', '')),
                    telefono=self._clean(row.get('Tel.', '')),
                    fax=self._clean(row.get('Fax', '')),
                    pagamento=self._clean(row.get('Codice Pagmento', '')),
                    descrizione_pagamento=self._clean(row.get('Descrizione Pagamento     ', '')),
                    banca=self._clean(row.get('Banca', '')),
                    filiale=self._clean(row.get('Filiale', '')),
                    abi=self._clean(row.get('ABI', '')),
                    cab=self._clean(row.get('CAB', '')),
                    conto_corrente=self._clean(row.get('C/C', '')),
                    iban=self._clean(row.get('IBAN', '')),
                    porto=self._clean(row.get('Porto', '')),
                    spedizione=self._clean(row.get('Spedizione', '')),
                    email=self._clean(row.get('E-mail', ''))
                )
                session.add(fornitore)

    def import_clienti(self, session: Session, filename):
        df = self._read_excel(filename)
        print(f"Importazione Clienti da {filename} ({len(df)} righe)...")
        for _, row in df.iterrows():
            codice = str(row.get('Codice', ''))
            
            existing = session.query(Cliente).filter_by(codice=codice).first()
            if not existing:
                cliente = Cliente(
                    codice=self._clean(row.get('Codice', '')),
                    codice_alternativo=self._clean(row.get('CLI codice alternativo', '')),
                    ragione_sociale=self._clean(row.get('Descrizione', '')),
                    indirizzo=self._clean(row.get('Indirizzo ', '')), # Fixed space
                    cap=self._clean(row.get('Cap', '')),
                    localita=self._clean(row.get('Città', '')),
                    provincia=self._clean(row.get('PR', '')),
                    nazione=self._clean(row.get('Nazione', '')),
                    partita_iva=self._clean(row.get(' P. IVA', '')), # Fixed space
                    codice_fiscale=self._clean(row.get('C. fiscale', '')),
                    telefono=self._clean(row.get('Telefono', '')),
                    email=self._clean(row.get('E-mail', '')),
                    cellulare=self._clean(row.get('Cellulare Fornitore', '')),
                    telefono2=self._clean(row.get('Telefono2', '')),
                    pagamento=self._clean(row.get('Codice Pagamento', '')),
                    descrizione_pagamento=self._clean(row.get('Descrizione Pagamento', '')),
                    banca=self._clean(row.get('Banca', '')),
                    filiale=self._clean(row.get('Filiale', '')),
                    abi=self._clean(row.get('ABI', '')),
                    cin=self._clean(row.get('CIN', '')),
                    conto_corrente=self._clean(row.get('c/c', '')),
                    iban=self._clean(row.get('IBAN', '')),
                    bic=self._clean(row.get('BIC', '')),
                    internet=self._clean(row.get('Internet', '')),
                    commento=self._clean(row.get('Commento', '')),
                    riferimento=self._clean(row.get('Riferimento', '')),
                    zona=self._clean(row.get('Zona', '')),
                    area=self._clean(row.get('Area    ', '')), # Fixed spaces
                    categoria=self._clean(row.get('Categoria', '')),
                    statistico=self._clean(row.get('Statistico', '')),
                    agente=self._clean(row.get('Agente', '')),
                    listino=self._clean(row.get('Listino ', '')) # Fixed space
                )
                session.add(cliente)

    def import_articoli(self, session: Session, filename):
        df = self._read_excel(filename)
        print(f"Importazione Articoli da {filename} ({len(df)} righe)...")
        for _, row in df.iterrows():
            codice = str(row.get('Codice', ''))
            
            existing = session.query(Articolo).filter_by(codice=codice).first()
            if not existing:
                articolo = Articolo(
                    codice=self._clean(row.get('Codice', '')),
                    descrizione=self._clean(row.get('Descrizione', '')),
                    um=self._clean(row.get('UM', ''))
                )
                session.add(articolo)

    def import_vendite(self, session: Session, filename):
        df = self._read_excel(filename)
        print(f"Importazione Fatture da {filename} ({len(df)} righe)...")
        
        # Cache for Invoice Aggregation: (Year, Numero) -> Fattura Object
        invoices_cache = {}
        
        # Sort by date ensures roughly chronological order, helpful but not strictly necessary if dict based
        # But we must be careful about duplicate invoice numbers across years if the file covers multiple years.
        
        for _, row in df.iterrows():
            # Parse Dates
            data_fattura_str = row.get('Data Fat', None)
            data_fattura = self._parse_date(data_fattura_str)
            
            data_ddt_str = row.get('Data Doc', None)
            data_ddt = self._parse_date(data_ddt_str)
            
            nr_fattura = row.get('Nr Fat', 0)
            try:
                nr_fattura = int(nr_fattura)
            except:
                nr_fattura = 0

            cliente_codice = str(row.get('Codice Cli', ''))
            
            # Key for cache
            year = data_fattura.year if data_fattura else 0
            inv_key = (year, nr_fattura)
            
            # Find or Create Fattura
            fattura = invoices_cache.get(inv_key)
            
            if not fattura:
                fattura = Fattura(
                    numero=nr_fattura,
                    data=data_fattura,
                    cliente_codice=self._clean(cliente_codice),
                    cliente_denominazione=self._clean(row.get('Descrizione cliente', '')),
                    causale=self._clean(row.get('Desc. Causale', '')),
                    totale=0.0
                )
                session.add(fattura)
                invoices_cache[inv_key] = fattura
            
            # Create Row
            totale_riga = self._parse_float(row.get('Importo_netto', 0))
            
            riga = RigaFattura(
                fattura=fattura,
                numero_ddt=self._clean(row.get('Nr Doc', '')),
                data_ddt=data_ddt,
                articolo_codice=self._clean(row.get('Codice Art', '')),
                descrizione=self._clean(row.get('Descrizione articolo', '')),
                quantita=self._parse_float(row.get('Quantità', 0)),
                prezzo_unitario=self._parse_float(row.get('Prezzo  unitario', 0)),
                totale_riga=totale_riga
            )
            session.add(riga)
            
            # Update Total
            fattura.totale += totale_riga

    def import_fattura_acquisto_sdi(self, filepath, session=None):
        """Punto di ingresso generico per importare una fattura da .p7m o .xml."""
        close_session = False
        if session is None:
            session = self.db_manager.get_session()
            close_session = True
            
        try:
            if filepath.lower().endswith('.p7m'):
                xml_bytes, err = self.extract_xml_from_p7m(filepath)
            else:
                with open(filepath, 'rb') as f:
                    xml_bytes = f.read()
                err = None
                
            if err:
                return False, f"Errore lettura/estrazione: {err}"
            
            data, err = self.parse_fattura_xml(xml_bytes)
            if err:
                return False, f"Errore parsing XML: {err}"
            
            # 1. Gestione Fornitore
            forn_data = data.get('fornitore', {})
            piva = forn_data.get('piva')
            if not piva:
                return False, "Partita IVA fornitore non trovata nella fattura"
            
            fornitore = session.query(Fornitore).filter_by(partita_iva=piva).first()
            if not fornitore:
                # Se non esiste, lo creiamo con i dati base dalla fattura
                # Nota: idealmente verrebbe usato il codice fornitore del gestionale se esistente, 
                # qui usiamo la PIVA come codice temporaneo se nuovo.
                denominazione = forn_data.get('denominazione') or f"{forn_data.get('nome','')} {forn_data.get('cognome','')}".strip()
                fornitore = Fornitore(
                    codice=f"NEW_{piva}",
                    ragione_sociale=denominazione,
                    partita_iva=piva,
                    indirizzo=forn_data.get('indirizzo'),
                    cap=forn_data.get('cap'),
                    localita=forn_data.get('comune'),
                    provincia=forn_data.get('provincia'),
                    nazione=forn_data.get('nazione')
                )
                session.add(fornitore)
                session.flush() # Per avere l'ID se necessario (anche se usiamo codici)
            
            # 2. Creazione Fattura
            ft_data = data.get('fattura', {})
            nr_fattura = ft_data.get('numero')
            data_fattura = self._parse_date(ft_data.get('data'))
            
            # Gestione Duplicati/Sovrascrittura
            existing = session.query(Fattura).filter_by(
                tipo='ACQUISTO',
                numero=nr_fattura,
                fornitore_codice=fornitore.codice
            ).first()
            
            if existing:
                # Se presente, la eliminiamo per sovrascriverla (inclusi i figli grazie al cascade)
                session.delete(existing)
                session.flush()
            
            fattura = Fattura(
                tipo='ACQUISTO',
                numero=nr_fattura,
                data=data_fattura,
                fornitore_codice=fornitore.codice,
                fornitore_denominazione=fornitore.ragione_sociale,
                totale=self._parse_float(ft_data.get('importo_totale')),
                causale=f"Import SDI: {os.path.basename(filepath)}"
            )
            session.add(fattura)
            
            # 3. Righe Dettaglio
            for r in data.get('righe', []):
                riga = RigaFattura(
                    fattura=fattura,
                    articolo_codice=r.get('codice_articolo'),
                    descrizione=r.get('descrizione'),
                    quantita=self._parse_float(r.get('quantita')),
                    prezzo_unitario=self._parse_float(r.get('prezzo_unitario')),
                    totale_riga=self._parse_float(r.get('prezzo_totale'))
                )
                session.add(riga)
            
            if close_session:
                session.commit()
            else:
                session.flush() # Assicura che i dati siano pronti per il commit esterno
                
            return True, f"Fattura n. {nr_fattura} importata correttamente."
        except Exception as e:
            return False, f"Errore importazione: {str(e)}"
        finally:
            if close_session:
                session.close()

    def delete_all_fatture_acquisto(self):
        """Elimina tutte le fatture di acquisto e le relative righe dal database."""
        session = self.db_manager.get_session()
        try:
            # Eliminiamo tutte le fatture di tipo ACQUISTO
            # Il cascade della relazione RigaFattura (se configurato) o l'eliminazione manuale 
            # assicurerà la pulizia dei figli.
            session.query(Fattura).filter_by(tipo='ACQUISTO').delete(synchronize_session=False)
            session.commit()
            return True, "Tutte le fatture di acquisto sono state eliminate."
        except Exception as e:
            session.rollback()
            return False, f"Errore durante l'eliminazione: {str(e)}"
        finally:
            session.close()
            

    # ─────────────────────────────────────────────────────────────────────────
    # IMPORT PDF ROBECCHI
    # ─────────────────────────────────────────────────────────────────────────

    # Dati fornitore Robecchi fissi
    ROBECCHI_CODICE       = 'ROBECCHI'
    ROBECCHI_PIVA         = '00843220161'
    ROBECCHI_DENOMINAZIONE = 'Robecchi Articoli Tecnici Srl'

    def import_pdf_robecchi(self, folder_path, progress_callback=None):
        """Importa documenti PDF Robecchi (fatture e conferme d'ordine leggibili).

        Scansiona ricorsivamente `folder_path`, estrae numero, data, totale e
        righe articolo da ogni PDF con testo selezionabile.

        Args:
            folder_path: percorso cartella radice (es. I:\\...\\Robecchi)
            progress_callback: callable(current, total, filename) opzionale

        Returns:
            dict con chiavi: 'imported', 'rows', 'skipped', 'errors' (list of (name, msg))
        """
        try:
            import pdfplumber
        except ImportError:
            return {'imported': 0, 'rows': 0, 'skipped': 0,
                    'errors': [('', 'pdfplumber non installato. Eseguire: pip install pdfplumber')]}

        result = {'imported': 0, 'rows': 0, 'skipped': 0, 'errors': []}

        # Raccolta ricorsiva dei PDF
        all_pdfs = []
        for root_dir, _, files in os.walk(folder_path):
            for f in files:
                if f.lower().endswith('.pdf'):
                    all_pdfs.append(os.path.join(root_dir, f))
        all_pdfs.sort()

        session = self.db_manager.get_session()
        try:
            for idx, pdf_path in enumerate(all_pdfs):
                name = os.path.basename(pdf_path)
                if progress_callback:
                    progress_callback(idx, len(all_pdfs), name)

                try:
                    ok, msg, n_rows = self._import_single_pdf_robecchi(pdf_path, session)
                    if ok is None:
                        # file saltato (scansione o offerta)
                        result['skipped'] += 1
                    elif ok:
                        result['imported'] += 1
                        result['rows'] += n_rows
                    else:
                        result['errors'].append((name, msg))
                except Exception as e:
                    result['errors'].append((name, f'Eccezione inattesa: {e}'))

            session.commit()
        except Exception as e:
            session.rollback()
            result['errors'].append(('', f'Errore fatale commit: {e}'))
        finally:
            session.close()

        return result

    def _import_single_pdf_robecchi(self, pdf_path, session):
        """Estrae e importa dati da un singolo PDF Robecchi.

        Returns:
            (True, msg, n_rows)  → importato con successo
            (False, msg, 0)      → errore da segnalare
            (None, msg, 0)       → saltato (scansione / offerta / già presente)
        """
        import pdfplumber

        name = os.path.basename(pdf_path)

        with pdfplumber.open(pdf_path) as pdf:
            # ── Estrazione testo ──────────────────────────────────────────
            full_text = ''
            all_tables = []
            for page in pdf.pages:
                t = page.extract_text() or ''
                full_text += t + '\n'
                for tab in (page.extract_tables() or []):
                    all_tables.append(tab)

        if not full_text.strip():
            return None, 'PDF-immagine, testo non estraibile', 0

        # ── Identificazione tipo documento ────────────────────────────────
        is_fattura = 'FATTURA' in full_text.upper() and re.search(r'N°\s*DOCUMENTO', full_text, re.I)
        is_ordine  = re.search(r"Conferma d.ordine\s+n\.\s*(\d+)\s+del\s+(\d{2}-\d{2}-\d{2,4})", full_text, re.I)
        is_offerta = re.search(r"Offerta\s*/\s*Offer\s+n\.", full_text, re.I)

        if is_offerta and not is_fattura:
            return None, 'Offerta/Preventivo — non è una fattura, saltato', 0

        if not is_fattura and not is_ordine:
            return None, 'Tipo documento non riconosciuto', 0

        # ── Estrazione numero e data ──────────────────────────────────────
        numero_doc = None
        data_doc   = None

        if is_fattura:
            # Cerca nella TABLE 0 che contiene N° DOCUMENTO e DATA DOC.
            for tab in all_tables:
                for row in tab:
                    for cell in (row or []):
                        if cell and 'N° DOCUMENTO' in str(cell).upper():
                            # La stessa cella contiene "\nXXXX"
                            parts = str(cell).split('\n')
                            if len(parts) >= 2:
                                numero_doc = parts[-1].strip()
                        if cell and 'DATA DOC.' in str(cell).upper():
                            parts = str(cell).split('\n')
                            if len(parts) >= 2:
                                data_doc = self._parse_robecchi_date(parts[-1].strip())
            # Fallback regex sul testo
            if not numero_doc:
                m = re.search(r'(?:N°\s*DOCUMENTO|Fattura\s+n\.)\s*(\d+)', full_text, re.I)
                if m:
                    numero_doc = m.group(1)
            if not data_doc:
                m = re.search(r'(?:DATA\s*DOC\.|del)\s+(\d{2}-\d{2}-\d{2,4})', full_text, re.I)
                if m:
                    data_doc = self._parse_robecchi_date(m.group(1))
        else:
            # Conferma d'ordine
            m = is_ordine
            numero_doc = m.group(1)
            data_doc   = self._parse_robecchi_date(m.group(2))

        if not numero_doc:
            return False, 'Numero documento non trovato', 0

        # ── Deduplicazione ────────────────────────────────────────────────
        existing = session.query(Fattura).filter_by(
            tipo='ACQUISTO',
            numero=numero_doc,
            fornitore_codice=self.ROBECCHI_CODICE
        ).first()
        if existing:
            return None, f'Fattura n.{numero_doc} già presente, saltata', 0

        # ── Estrazione totale ─────────────────────────────────────────────
        totale = 0.0
        if is_fattura:
            m = re.search(r'TOTALE\s+FATTURA[\s\S]{0,30}?EUR\s*([\d.,]+)', full_text, re.I)
            if m:
                totale = self._parse_italian_float(m.group(1))
        else:
            # Conferma d'ordine: "€ X.XXX,XX" prima di INSERITO DA (con \r\n o \n)
            m = re.search(r'€\s*([\d.,]+)\s*[\r\n]+\s*INSERITO', full_text, re.I)
            if not m:  # fallback senza newline tra cifra e INSERITO
                m = re.search(r'€\s*([\d.,]+)\s*INSERITO', full_text, re.I)
            if m:
                totale = self._parse_italian_float(m.group(1))

        # ── Garantisce esistenza fornitore Robecchi ───────────────────────
        fornitore = session.query(Fornitore).filter_by(codice=self.ROBECCHI_CODICE).first()
        if not fornitore:
            fornitore = Fornitore(
                codice=self.ROBECCHI_CODICE,
                ragione_sociale=self.ROBECCHI_DENOMINAZIONE,
                partita_iva=self.ROBECCHI_PIVA,
                localita='GRUMELLO DEL MONTE',
                provincia='BG',
                nazione='IT',
                email='robecchisas@robecchi.com',
                telefono='035 832 422',
            )
            session.add(fornitore)
            session.flush()

        # ── Creazione Fattura ─────────────────────────────────────────────
        doc_type = 'FATTURA' if is_fattura else 'ORDINE'
        fattura = Fattura(
            tipo='ACQUISTO',
            numero=numero_doc,
            data=data_doc,
            fornitore_codice=self.ROBECCHI_CODICE,
            fornitore_denominazione=self.ROBECCHI_DENOMINAZIONE,
            totale=totale,
            causale=f'PDF Robecchi {doc_type}: {os.path.basename(pdf_path)}',
        )
        session.add(fattura)
        session.flush()

        # ── Estrazione righe articolo ─────────────────────────────────────
        n_rows = self._extract_rows_pdf_robecchi(full_text, fattura, session)

        # ── Fallback totale: somma righe se totale non estratto ───────────
        if totale == 0.0 and n_rows > 0:
            fattura.totale = sum(
                self._parse_italian_float(str(r.totale_riga))
                for r in fattura.righe
            )
        else:
            fattura.totale = totale

        return True, f'{doc_type} n.{numero_doc} importata ({n_rows} righe)', n_rows

    # Regex per una riga articolo Robecchi nel testo piatto:
    # C001578-XXXX  DESCRIZIONE  UM  QTY  PREZZO_UNIT  TOTALE  [...]
    _RX_RIGA = re.compile(
        r'^(C\d{6}-\d{4})\s+'       # codice articolo (gruppo 1)
        r'(.+?)\s+'                   # descrizione (gruppo 2)
        r'(NR|MT|KG|LT|CONF|PZ)\s+'  # unità di misura (gruppo 3)
        r'([\d.,]+)\s+'               # quantità (gruppo 4)
        r'([\d.,]+)\s+'               # prezzo unitario (gruppo 5)
        r'([\d.,]+)',                  # totale riga (gruppo 6)
        re.IGNORECASE | re.MULTILINE
    )

    def _extract_rows_pdf_robecchi(self, full_text, fattura, session):
        """Estrae le righe articolo dal testo e le associa alla fattura."""
        n_rows = 0
        for m in self._RX_RIGA.finditer(full_text):
            codice_raw = m.group(1).upper()
            descrizione = m.group(2).strip()
            um          = m.group(3).upper()
            quantita    = self._parse_italian_float(m.group(4))
            prezzo_unit = self._parse_italian_float(m.group(5))
            totale_riga = self._parse_italian_float(m.group(6))

            # Skip righe di intestazione colonne
            if not quantita and not prezzo_unit:
                continue

            # Matching articolo nel DB (codice esatto)
            articolo_codice = None
            articolo = session.query(Articolo).filter_by(codice=codice_raw).first()
            if articolo:
                articolo_codice = articolo.codice
            else:
                # Fuzzy: primo token della descrizione > 5 char
                keywords = [w for w in descrizione.split() if len(w) > 5]
                if keywords:
                    kw = keywords[0]
                    articolo = session.query(Articolo).filter(
                        Articolo.descrizione.ilike(f'%{kw}%')
                    ).first()
                    if articolo:
                        articolo_codice = articolo.codice

            riga = RigaFattura(
                fattura=fattura,
                articolo_codice=articolo_codice or codice_raw,
                descrizione=descrizione,
                quantita=quantita,
                prezzo_unitario=prezzo_unit,
                totale_riga=totale_riga,
            )
            session.add(riga)
            n_rows += 1

        return n_rows

    def _parse_robecchi_date(self, s):
        """Converte date Robecchi: DD-MM-YY o DD-MM-YYYY → date ISO."""
        if not s:
            return None
        s = s.strip()
        for fmt in ('%d-%m-%y', '%d-%m-%Y'):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                pass
        return None

    def import_fattura_acquisto_p7m(self, filepath):
        """Mantenuto per compatibilità, delega al nuovo metodo generico."""
        return self.import_fattura_acquisto_sdi(filepath)

    def batch_import_from_folders(self, folder_paths, progress_callback=None):
        """Scansiona cartelle e sottocartelle, importa file SDI univoci."""
        all_files = []
        for folder in folder_paths:
            if not os.path.exists(folder): continue
            for root, dirs, files in os.walk(folder):
                for f in files:
                    # Esclui file di metadati SDI che non sono fatture
                    if "_metadato" in f.lower():
                        continue
                    if f.lower().endswith(('.p7m', '.xml')):
                        all_files.append(os.path.join(root, f))
        
        if not all_files:
            return 0, 0, []

        session = self.db_manager.get_session()
        success_count = 0
        error_count = 0
        errors = []
        
        # Logica di deduplicazione: raggruppiamo per nome file base (senza estensione)
        # In genere le fatture SDI scaricate hanno nomi file univoci.
        # Spesso lo stesso documento è presente sia come .xml (SD) sia come .p7m.
        # Preferiamo il file .xml se presente, in quanto più pulito e facile da leggere.
        file_map = {} # basename -> path
        for fpath in all_files:
            fname = os.path.basename(fpath).lower()
            # Identificazione basename: rimuoviamo sia .p7m che .xml
            basename = fname
            if basename.endswith('.p7m'): basename = basename[:-4]
            if basename.endswith('.xml'): basename = basename[:-4]
            
            # Se abbiamo già un file per questo basename, decidiamo quale tenere
            if basename not in file_map:
                file_map[basename] = fpath
            else:
                current_path = file_map[basename]
                # Priorità: XML (SD) > P7M
                if fpath.lower().endswith('.xml'):
                    file_map[basename] = fpath
                elif current_path.lower().endswith('.p7m') and fpath.lower().endswith('.xml'):
                    file_map[basename] = fpath

        unique_files = list(file_map.values())
        total = len(unique_files)
        
        try:
            for i, fpath in enumerate(unique_files):
                if progress_callback:
                    progress_callback(i, total, os.path.basename(fpath))
                
                success, msg = self.import_fattura_acquisto_sdi(fpath, session=session)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{os.path.basename(fpath)}: {msg}")
            
            session.commit()
        except Exception as e:
            session.rollback()
            errors.append(f"Errore fatale batch: {str(e)}")
        finally:
            session.close()
            
        return success_count, error_count, errors

    def extract_xml_from_p7m(self, filepath):
        """Estrae il payload XML da un file .p7m gestendo formati binari, Base64 e line-based."""
        try:
            with open(filepath, 'rb') as f:
                raw_data = f.read()
            
            # 1. Pulizia preliminare e gestione encoding testuale (Base64/PEM)
            data = raw_data.replace(b'\x00', b'')
            
            # 2. Supporto Base64 (alcuni P7M scaricati da portali sono Base64 PEM)
            if b'BASE64' in data.upper() or (not b'<' in data and len(data) > 100):
                import base64
                import re
                # Cerchiamo blocchi Base64
                b64_matches = re.findall(rb'[A-Za-z0-9+/=\s]{100,}', data)
                for match in b64_matches:
                    try:
                        decoded = base64.b64decode(match.strip())
                        if b'<?xml' in decoded or b'<Fattura' in decoded:
                            data = decoded
                            break
                    except: continue

            # 3. STRATEGIA BINARIA CHIRURGICA
            start = -1
            for t in [b'<?xml', b'<p:FatturaElettronica', b'<FatturaElettronica']:
                pos = data.lower().find(t.lower())
                if pos != -1:
                    if start == -1 or pos < start: start = pos
            
            if start != -1:
                end = -1
                for t in [b'</p:FatturaElettronica>', b'</FatturaElettronica>']:
                    pos = data.lower().find(t.lower(), start)
                    if pos != -1:
                        potential_end = pos + len(t)
                        if end == -1 or potential_end < end: end = potential_end
                
                if end != -1:
                    return data[start:end], None

            # 4. STRATEGIA LINE-BASED (Focus sulla "quarta riga" o simili)
            lines = data.splitlines()
            xml_accumulator = []
            capturing = False
            for line in lines:
                line_lower = line.lower()
                if not capturing:
                    for t in [b'<?xml', b'<p:FatturaElettronica', b'<FatturaElettronica']:
                        if t.lower() in line_lower:
                            capturing = True
                            pos = line_lower.find(t.lower())
                            xml_accumulator.append(line[pos:])
                            break
                else:
                    end_found = False
                    for t in [b'</p:FatturaElettronica>', b'</FatturaElettronica>']:
                        if t.lower() in line_lower:
                            pos = line_lower.find(t.lower())
                            xml_accumulator.append(line[:pos + len(t)])
                            end_found = True
                            break
                    if end_found: break
                    xml_accumulator.append(line)
            
            if xml_accumulator:
                return b"".join(xml_accumulator), None
                
            return None, "Struttura XML non identificata (probabile file PDF o corrotto)"
            
        except Exception as e:
            return None, f"Errore estrazione: {str(e)}"

    def parse_fattura_xml(self, xml_bytes):
        """Parsa l'XML con auto-rilevamento encoding, pulizia radicale e regex fallback."""
        import re
        
        # 1. Rilevamento Encoding
        encoding = 'utf-8'
        m = re.search(rb'encoding=["\'](.*?)["\']', xml_bytes[:800])
        if m:
            encoding = m.group(1).decode('ascii', errors='ignore')
        
        def try_parse(b_data):
            try:
                # Proviamo a pulire i byte binari spazzatura (non-printable tranne tab/newline)
                # Lasciamo solo il range ASCII stampabile e i byte sopra 127 se sembrano validi UTF-8
                clean = re.sub(rb'[^\x09\x0A\x0D\x20-\x7E\xA0-\xFF]', b' ', b_data)
                return ET.fromstring(clean)
            except:
                try:
                    # Strip namespace radicale
                    text = b_data.decode(encoding, errors='replace')
                    text = re.sub(r'\s+xmlns(:[a-zA-Z0-9]+)?="[^"]*"', '', text)
                    text = re.sub(r'</?[a-zA-Z0-9]+:', '<', text)
                    # Clipping post-chiusura
                    for t in ['</FatturaElettronica>', '</p:FatturaElettronica>']:
                        pos = text.lower().rfind(t.lower())
                        if pos != -1:
                            text = text[:pos + len(t)]
                            break
                    return ET.fromstring(text.encode('utf-8'))
                except:
                    return None

        root = try_parse(xml_bytes)
        if root is not None:
            return self._extract_data_from_root(root), None

        # FALLBACK REGEX: Se ElementTree fallisce, estraiamo i dati via Regex
        # Utile per file "irrecuperabili" strutturalmente ma contenenti testo leggibile
        try:
            text = xml_bytes.decode(encoding, errors='replace')
            
            def get_val(pattern, txt):
                m = re.search(pattern, txt, re.IGNORECASE | re.DOTALL)
                return m.group(1).strip() if m else ""

            res = {
                'fornitore': {
                    'piva': get_val(r'<IdCodice>([^<]+)', text),
                    'denominazione': get_val(r'<Denominazione>([^<]+)', text) or get_val(r'<Nome>([^<]+)', text),
                },
                'fattura': {
                    'numero': get_val(r'<Numero>([^<]+)', text),
                    'data': get_val(r'<Data>([^<]+)', text),
                    'importo_totale': get_val(r'<ImportoTotaleDocumento>([^<]+)', text),
                },
                'righe': []
            }
            
            # Estrazione righe semplificata via regex
            line_matches = re.findall(r'<DettaglioLinee>(.*?)</DettaglioLinee>', text, re.DOTALL)
            for l_txt in line_matches:
                res['righe'].append({
                    'descrizione': get_val(r'<Descrizione>([^<]+)', l_txt),
                    'quantita': self._parse_float(get_val(r'<Quantita>([^<]+)', l_txt)),
                    'prezzo_unitario': self._parse_float(get_val(r'<PrezzoUnitario>([^<]+)', l_txt)),
                    'prezzo_totale': self._parse_float(get_val(r'<PrezzoTotale>([^<]+)', l_txt)),
                    'codice_articolo': get_val(r'<CodiceValore>([^<]+)', l_txt),
                })
            
            if res['fattura']['numero']:
                return res, None
        except: pass

        return None, "Impossibile recuperare i dati della fattura (XML e Regex falliti)"

    def _extract_data_from_root(self, root):
        """Metodo helper per estrarre i dati dalla struttura ET già parsata."""
        def find_text(el, tag_name):
            for child in el.iter():
                tag = child.tag.split('}')[-1]
                if tag == tag_name:
                    return child.text.strip() if child.text else ''
            return ''

        res = {'fornitore': {}, 'cliente': {}, 'fattura': {}, 'righe': []}
        
        # Blocchi principali
        header = None
        for el in root.iter():
            if el.tag.split('}')[-1] == 'FatturaElettronicaHeader':
                header = el
                break
        if header is None: header = root
        
        ced = None
        for el in header.iter():
            if el.tag.split('}')[-1] == 'CedentePrestatore':
                ced = el
                break
        
        if ced is not None:
            res['fornitore'] = {
                'denominazione': find_text(ced, 'Denominazione'),
                'nome': find_text(ced, 'Nome'),
                'cognome': find_text(ced, 'Cognome'),
                'piva': find_text(ced, 'IdCodice'),
                'indirizzo': find_text(ced, 'Indirizzo'),
                'cap': find_text(ced, 'CAP'),
                'comune': find_text(ced, 'Comune'),
                'provincia': find_text(ced, 'Provincia'),
                'nazione': find_text(ced, 'Nazione'),
            }
        
        body = None
        for el in root.iter():
            if el.tag.split('}')[-1] == 'FatturaElettronicaBody':
                body = el
                break
        if body is None: body = root
        
        dg = None
        for el in body.iter():
            if el.tag.split('}')[-1] == 'DatiGeneraliDocumento':
                dg = el
                break
        
        if dg is not None:
            res['fattura'] = {
                'numero': find_text(dg, 'Numero'),
                'data': find_text(dg, 'Data'),
                'importo_totale': find_text(dg, 'ImportoTotaleDocumento'),
            }
        
        # Righe Dettaglio - Filtraggio Restrittivo
        excluded_keywords = ['DDT', 'ORDINE', 'SPESE', 'TRASPORTO', 'IMBALLO', 'BOLLO', 'CONTRIBUTO', 'RIF.', 'RECA', 'CAUSALE']
        
        for line in body.iter():
            if line.tag.split('}')[-1] == 'DettaglioLinee':
                desc = find_text(line, 'Descrizione')
                quant = self._parse_float(find_text(line, 'Quantita'))
                prezzo = self._parse_float(find_text(line, 'PrezzoUnitario'))
                totale = self._parse_float(find_text(line, 'PrezzoTotale'))
                codice = find_text(line, 'CodiceValore')
                
                if not codice: codice = ""
                
                if quant <= 0 or prezzo <= 0 or totale <= 0: continue
                
                desc_upper = desc.upper()
                if any(kw in desc_upper for kw in excluded_keywords): continue
                
                if not codice and len(desc) > 100 and " " in desc:
                    if not any(char.isdigit() for char in desc[:10]): continue

                res['righe'].append({
                    'descrizione': desc,
                    'quantita': quant,
                    'unita_misura': find_text(line, 'UnitaMisura'),
                    'prezzo_unitario': prezzo,
                    'prezzo_totale': totale,
                    'codice_articolo': codice,
                })
        
        return res

    def _parse_date(self, val):
        if pd.isna(val) or val == '': return None
        try:
            return pd.to_datetime(val).date()
        except:
            return None

    def _parse_float(self, val):
        try:
            # Rimuove eventuali simboli valuta o spazi prima del cast
            clean_val = str(val).replace('€', '').replace('$', '').strip()
            return float(clean_val.replace(',', '.'))
        except:
            return 0.0

    def _parse_italian_float(self, val):
        """Converte numeri in formato italiano (1.067,50) in float.

        Gestisce sia il formato italiano (punto=migliaia, virgola=decimale)
        sia il formato semplice (solo virgola=decimale, es. '300,00').
        """
        try:
            s = str(val).replace('€', '').replace('$', '').replace(' ', '').strip()
            if not s:
                return 0.0
            # Se ha sia punto che virgola → formato IT: 1.067,50
            if ',' in s and '.' in s:
                s = s.replace('.', '').replace(',', '.')
            elif ',' in s:
                # Solo virgola → decimale italiano: 300,00
                s = s.replace(',', '.')
            # else: solo punto → standard anglosassone già corretto
            return float(s)
        except:
            return 0.0


if __name__ == "__main__":
    db = DatabaseManager()
    dm = DataManager(db)
    dm.import_all()
