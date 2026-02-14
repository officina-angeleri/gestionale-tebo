import pandas as pd
from sqlalchemy.orm import Session
from database import DatabaseManager, Cliente, Fornitore, Articolo, Fattura, RigaFattura
from datetime import datetime
import os

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

    def _parse_date(self, val):
        if pd.isna(val) or val == '': return None
        try:
            return pd.to_datetime(val).date()
        except:
            return None

    def _parse_float(self, val):
        try:
            return float(str(val).replace(',', '.'))
        except:
            return 0.0

if __name__ == "__main__":
    db = DatabaseManager()
    dm = DataManager(db)
    dm.import_all()
