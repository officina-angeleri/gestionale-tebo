from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os

Base = declarative_base()

class Cliente(Base):
    __tablename__ = 'clienti'
    
    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, index=True)
    codice_alternativo = Column(String)
    ragione_sociale = Column(String)  # 'Descrizione'
    indirizzo = Column(String)
    cap = Column(String)
    localita = Column(String)      # 'Città'
    provincia = Column(String)     # 'PR'
    nazione = Column(String)
    partita_iva = Column(String)   # 'P. IVA'
    codice_fiscale = Column(String)# 'C. fiscale'
    telefono = Column(String)
    email = Column(String)         # 'E-mail'
    cellulare = Column(String)     # 'Cellulare Fornitore'
    telefono2 = Column(String)
    pagamento = Column(String)     # 'Codice Pagamento'
    descrizione_pagamento = Column(String)  # 'Descrizione Pagamento'
    banca = Column(String)
    filiale = Column(String)
    abi = Column(String)
    cin = Column(String)
    conto_corrente = Column(String)# 'c/c'
    iban = Column(String)
    bic = Column(String)
    internet = Column(String)
    commento = Column(String)
    riferimento = Column(String)
    zona = Column(String)
    area = Column(String)
    categoria = Column(String)     # 'Categoria'
    statistico = Column(String)
    agente = Column(String)
    listino = Column(String)

    # fatture relationship will be re-added when cross-referencing is implemented

class Fornitore(Base):
    __tablename__ = 'fornitori'
    
    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, index=True)
    ragione_sociale = Column(String)
    indirizzo_esteso = Column(String)
    indirizzo = Column(String)
    cap = Column(String)
    localita = Column(String)
    provincia = Column(String)
    nazione = Column(String)
    codice_fiscale = Column(String) # 'C. fisc.'
    partita_iva = Column(String) # 'P. IVA'
    partita_iva_intra = Column(String) # 'IVA Intra'
    telefono = Column(String)
    fax = Column(String)
    pagamento = Column(String) # 'Codice Pagmento'
    descrizione_pagamento = Column(String)
    banca = Column(String)
    filiale = Column(String)
    abi = Column(String)
    cab = Column(String)
    conto_corrente = Column(String) # 'C/C'
    iban = Column(String)
    porto = Column(String)
    spedizione = Column(String)
    email = Column(String)

class Articolo(Base):
    __tablename__ = 'articoli'
    
    id = Column(Integer, primary_key=True)
    codice = Column(String, unique=True, index=True)
    descrizione = Column(String)
    prezzo = Column(Float, default=0.0) # Might be missing in xls
    um = Column(String) # 'UM'
    peso_lordo = Column(Float)
    peso_netto = Column(Float)
    
    # fornitore_codice seems missing in Articoli file

class Fattura(Base):
    __tablename__ = 'fatture'

    id = Column(Integer, primary_key=True)
    tipo = Column(String, default='VENDITA') # 'VENDITA' o 'ACQUISTO'
    numero = Column(Integer)  # 'Nr Fat'
    data = Column(Date)       # 'Data Fat'
    cliente_codice = Column(String, nullable=True)  # 'Codice Cli' - no FK for now
    cliente_denominazione = Column(String)  # 'Descrizione cliente' - text from Excel
    fornitore_codice = Column(String, nullable=True)
    fornitore_denominazione = Column(String, nullable=True)
    totale = Column(Float, default=0.0)
    causale = Column(String) # 'Desc. Causale'

    righe = relationship("RigaFattura", back_populates="fattura", cascade="all, delete-orphan")

class RigaFattura(Base):
    __tablename__ = 'righe_fattura'
    
    id = Column(Integer, primary_key=True)
    fattura_id = Column(Integer, ForeignKey('fatture.id'))
    
    # Dati originali riga
    data_ddt = Column(Date) # 'Data Doc' (DDT)
    numero_ddt = Column(String) # 'Nr Doc' (DDT)
    
    articolo_codice = Column(String, ForeignKey('articoli.codice'), nullable=True) # 'Codice Art'
    descrizione = Column(String) # 'Descrizione articolo'
    quantita = Column(Float) # 'Quantità'
    prezzo_unitario = Column(Float) # 'Prezzo  unitario'
    totale_riga = Column(Float) # 'Importo_netto'

    fattura = relationship("Fattura", back_populates="righe")
    articolo = relationship("Articolo")

class DatabaseManager:
    def __init__(self, db_path='tebo.db'):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()
