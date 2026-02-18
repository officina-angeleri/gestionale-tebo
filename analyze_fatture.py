"""
Analisi fatture elettroniche SDI (.p7m) per il progetto gestionale-tebo.
Estrae il payload XML dal file .p7m (CAdES) e ne analizza la struttura.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

def extract_xml_from_p7m(filepath):
    """Estrae il payload XML da un file .p7m (CAdES signed)."""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Cerca inizio XML
    start = data.find(b'<?xml')
    if start == -1:
        start = data.find(b'<p:FatturaElettronica')
    if start == -1:
        start = data.find(b'<FatturaElettronica')
    
    if start == -1:
        return None, "XML non trovato nel file"
    
    # Cerca fine XML
    for end_tag in [b'</p:FatturaElettronica>', b'</FatturaElettronica>']:
        end = data.rfind(end_tag)
        if end > start:
            xml_bytes = data[start:end + len(end_tag)]
            # Rimuovi byte nulli
            xml_clean = xml_bytes.replace(b'\x00', b'')
            return xml_clean, None
    
    return None, "Tag di chiusura non trovato"


def parse_fattura(xml_bytes):
    """Parsa l'XML della fattura elettronica e restituisce i dati strutturati."""
    # Registra namespace
    ns = {
        'p': 'http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2',
        'ds': 'http://www.w3.org/2000/09/xmldsig#',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        # Prova a rimuovere namespace prefix problematici
        xml_str = xml_bytes.decode('utf-8', errors='replace')
        # Rimuovi namespace prefix
        xml_str = re.sub(r'<p:', '<', xml_str)
        xml_str = re.sub(r'</p:', '</', xml_str)
        xml_str = re.sub(r' xmlns[^"]*"[^"]*"', '', xml_str)
        xml_str = re.sub(r' xsi:[^"]*"[^"]*"', '', xml_str)
        try:
            root = ET.fromstring(xml_str.encode('utf-8'))
        except ET.ParseError as e2:
            return None, f"Errore parsing XML: {e2}"
    
    def find_text(el, *paths):
        """Cerca un elemento in più path alternativi."""
        for path in paths:
            found = el.find(path)
            if found is not None and found.text:
                return found.text.strip()
        return ''
    
    result = {}
    
    # Header - Dati Trasmissione
    header = root.find('FatturaElettronicaHeader')
    if header is None:
        header = root
    
    # Cedente (Fornitore)
    cedente = header.find('.//CedentePrestatore')
    if cedente is not None:
        result['fornitore'] = {
            'denominazione': find_text(cedente, './/Denominazione'),
            'nome': find_text(cedente, './/Nome'),
            'cognome': find_text(cedente, './/Cognome'),
            'piva': find_text(cedente, './/IdCodice'),
            'indirizzo': find_text(cedente, './/Indirizzo'),
            'cap': find_text(cedente, './/CAP'),
            'comune': find_text(cedente, './/Comune'),
            'provincia': find_text(cedente, './/Provincia'),
            'nazione': find_text(cedente, './/Nazione'),
        }
    
    # Cessionario (Cliente = TEBO)
    cessionario = header.find('.//CessionarioCommittente')
    if cessionario is not None:
        result['cliente'] = {
            'denominazione': find_text(cessionario, './/Denominazione'),
            'piva': find_text(cessionario, './/IdCodice'),
        }
    
    # Body - Dati Generali
    body = root.find('FatturaElettronicaBody')
    if body is None:
        body = root
    
    dati_gen = body.find('.//DatiGeneraliDocumento')
    if dati_gen is not None:
        result['fattura'] = {
            'tipo_documento': find_text(dati_gen, 'TipoDocumento'),
            'numero': find_text(dati_gen, 'Numero'),
            'data': find_text(dati_gen, 'Data'),
            'importo_totale': find_text(dati_gen, 'ImportoTotaleDocumento'),
        }
    
    # Righe fattura
    righe = []
    for linea in body.findall('.//DettaglioLinee'):
        riga = {
            'numero_linea': find_text(linea, 'NumeroLinea'),
            'codice_articolo': '',
            'descrizione': find_text(linea, 'Descrizione'),
            'quantita': find_text(linea, 'Quantita'),
            'unita_misura': find_text(linea, 'UnitaMisura'),
            'prezzo_unitario': find_text(linea, 'PrezzoUnitario'),
            'sconto': '',
            'prezzo_totale': find_text(linea, 'PrezzoTotale'),
            'aliquota_iva': find_text(linea, 'AliquotaIVA'),
        }
        # Codice articolo
        for cod in linea.findall('.//CodiceArticolo'):
            tipo = find_text(cod, 'CodiceTipo')
            valore = find_text(cod, 'CodiceValore')
            if tipo and valore:
                riga['codice_articolo'] += f"{tipo}:{valore} "
        # Sconti
        sconti = []
        for sconto in linea.findall('.//ScontoMaggiorazione'):
            tipo = find_text(sconto, 'Tipo')
            perc = find_text(sconto, 'Percentuale')
            imp = find_text(sconto, 'Importo')
            if perc:
                sconti.append(f"{tipo} {perc}%")
            elif imp:
                sconti.append(f"{tipo} €{imp}")
        riga['sconto'] = ', '.join(sconti)
        righe.append(riga)
    
    result['righe'] = righe
    
    # Riepilogo IVA
    result['riepilogo_iva'] = []
    for riepilogo in body.findall('.//DatiRiepilogo'):
        result['riepilogo_iva'].append({
            'aliquota': find_text(riepilogo, 'AliquotaIVA'),
            'imponibile': find_text(riepilogo, 'ImponibileImporto'),
            'imposta': find_text(riepilogo, 'Imposta'),
        })
    
    # Pagamento
    dati_pag = body.find('.//DatiPagamento')
    if dati_pag is not None:
        result['pagamento'] = {
            'condizioni': find_text(dati_pag, 'CondizioniPagamento'),
            'modalita': find_text(dati_pag, 'ModalitaPagamento'),
            'data_scadenza': find_text(dati_pag, 'DataScadenzaPagamento'),
            'importo': find_text(dati_pag, 'ImportoPagamento'),
        }
    
    return result, None


def print_analysis(filepath):
    print(f"\n{'='*60}")
    print(f"FILE: {os.path.basename(filepath)}")
    print(f"{'='*60}")
    
    xml_bytes, err = extract_xml_from_p7m(filepath)
    if err:
        print(f"ERRORE estrazione: {err}")
        return
    
    print(f"XML estratto: {len(xml_bytes)} bytes")
    
    data, err = parse_fattura(xml_bytes)
    if err:
        print(f"ERRORE parsing: {err}")
        # Mostra XML grezzo
        print("\nXML grezzo (primi 2000 chars):")
        print(xml_bytes[:2000].decode('utf-8', errors='replace'))
        return
    
    if 'fornitore' in data:
        f = data['fornitore']
        print(f"\n📦 FORNITORE:")
        print(f"  Denominazione: {f.get('denominazione') or f.get('nome','') + ' ' + f.get('cognome','')}")
        print(f"  P.IVA: {f.get('piva')}")
        print(f"  Indirizzo: {f.get('indirizzo')}, {f.get('cap')} {f.get('comune')} ({f.get('provincia')}) {f.get('nazione')}")
    
    if 'fattura' in data:
        ft = data['fattura']
        print(f"\n📄 FATTURA:")
        print(f"  Tipo: {ft.get('tipo_documento')}")
        print(f"  Numero: {ft.get('numero')}")
        print(f"  Data: {ft.get('data')}")
        print(f"  Totale: €{ft.get('importo_totale')}")
    
    if 'righe' in data:
        print(f"\n📋 RIGHE ({len(data['righe'])} righe):")
        for r in data['righe']:
            print(f"  Linea {r['numero_linea']}: {r['descrizione'][:50]}")
            print(f"    Codice: {r['codice_articolo'] or 'N/A'}")
            print(f"    Qtà: {r['quantita']} {r['unita_misura']} | Prezzo: €{r['prezzo_unitario']} | Totale: €{r['prezzo_totale']}")
            print(f"    IVA: {r['aliquota_iva']}% | Sconto: {r['sconto'] or 'Nessuno'}")
    
    if 'riepilogo_iva' in data:
        print(f"\n💰 RIEPILOGO IVA:")
        for r in data['riepilogo_iva']:
            print(f"  Aliquota {r['aliquota']}%: Imponibile €{r['imponibile']} | IVA €{r['imposta']}")
    
    if 'pagamento' in data:
        p = data['pagamento']
        print(f"\n💳 PAGAMENTO:")
        print(f"  Condizioni: {p.get('condizioni')} | Modalità: {p.get('modalita')}")
        print(f"  Scadenza: {p.get('data_scadenza')} | Importo: €{p.get('importo')}")
    
    # Verifica campi richiesti
    print(f"\n✅ VERIFICA CAMPI RICHIESTI:")
    campi = {
        'Numero fattura': bool(data.get('fattura', {}).get('numero')),
        'Data fattura': bool(data.get('fattura', {}).get('data')),
        'Dati fornitore': bool(data.get('fornitore', {}).get('denominazione')),
        'Righe presenti': len(data.get('righe', [])) > 0,
        'Descrizione riga': any(r.get('descrizione') for r in data.get('righe', [])),
        'Quantità': any(r.get('quantita') for r in data.get('righe', [])),
        'Prezzo unitario': any(r.get('prezzo_unitario') for r in data.get('righe', [])),
        'Totale riga': any(r.get('prezzo_totale') for r in data.get('righe', [])),
        'IVA': any(r.get('aliquota_iva') for r in data.get('righe', [])),
        'Codice articolo': any(r.get('codice_articolo') for r in data.get('righe', [])),
        'Sconti': any(r.get('sconto') for r in data.get('righe', [])),
    }
    for campo, presente in campi.items():
        stato = '✓' if presente else '✗'
        print(f"  {stato} {campo}")


# Analizza entrambi i file
files = [
    'Fatture fornitori esempio/IT01879020517A2025_aDYAY.xml.p7m',
    'Fatture fornitori esempio/IT01879020517A2025_azoRL.xml.p7m',
]

for f in files:
    if os.path.exists(f):
        print_analysis(f)
    else:
        print(f"File non trovato: {f}")
