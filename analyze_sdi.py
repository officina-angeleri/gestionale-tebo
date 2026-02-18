import sys, re
sys.stdout.reconfigure(encoding='utf-8')

def extract_tags(data, tag):
    pattern = ('<' + tag + '>([^<]*)</' + tag + '>').encode('ascii')
    matches = re.findall(pattern, data)
    return [m.decode('ascii', errors='replace') for m in matches]

def extract_blocks(data, tag):
    open_tag = ('<' + tag + '>').encode('ascii')
    close_tag = ('</' + tag + '>').encode('ascii')
    results = []
    start = 0
    while True:
        s = data.find(open_tag, start)
        if s == -1:
            break
        e = data.find(close_tag, s)
        if e == -1:
            break
        block = data[s:e+len(close_tag)]
        results.append(block)
        start = e + len(close_tag)
    return results

files = [
    'IT01879020517A2025_aDYAY.xml.p7m',
    'IT01879020517A2025_azoRL.xml.p7m',
]

for filename in files:
    filepath = 'Fatture fornitori esempio/' + filename
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print('=== ' + filename + ' ===')
    print('Numero:', extract_tags(data, 'Numero'))
    print('Data:', extract_tags(data, 'Data'))
    print('TipoDocumento:', extract_tags(data, 'TipoDocumento'))
    print('ImportoTotaleDocumento:', extract_tags(data, 'ImportoTotaleDocumento'))
    print('Denominazione:', extract_tags(data, 'Denominazione'))
    print('IdCodice (PIVA):', extract_tags(data, 'IdCodice'))
    print('Indirizzo:', extract_tags(data, 'Indirizzo'))
    print('Comune:', extract_tags(data, 'Comune'))
    print('Provincia:', extract_tags(data, 'Provincia'))
    print()
    print('--- RIGHE DETTAGLIO ---')
    righe = extract_blocks(data, 'DettaglioLinee')
    print('Numero righe trovate:', len(righe))
    for i, riga in enumerate(righe):
        print('  Riga ' + str(i+1) + ':')
        print('    NumeroLinea:', extract_tags(riga, 'NumeroLinea'))
        print('    Descrizione:', extract_tags(riga, 'Descrizione'))
        print('    Quantita:', extract_tags(riga, 'Quantita'))
        print('    UnitaMisura:', extract_tags(riga, 'UnitaMisura'))
        print('    PrezzoUnitario:', extract_tags(riga, 'PrezzoUnitario'))
        print('    PrezzoTotale:', extract_tags(riga, 'PrezzoTotale'))
        print('    AliquotaIVA:', extract_tags(riga, 'AliquotaIVA'))
        sconti = extract_blocks(riga, 'ScontoMaggiorazione')
        if sconti:
            for s in sconti:
                print('    Sconto: Tipo=' + str(extract_tags(s,'Tipo')) + ' Perc=' + str(extract_tags(s,'Percentuale')) + ' Imp=' + str(extract_tags(s,'Importo')))
        codici = extract_blocks(riga, 'CodiceArticolo')
        if codici:
            for c in codici:
                print('    CodiceArticolo: Tipo=' + str(extract_tags(c,'CodiceTipo')) + ' Val=' + str(extract_tags(c,'CodiceValore')))
    print()
    print('--- RIEPILOGO IVA ---')
    riep = extract_blocks(data, 'DatiRiepilogo')
    for r in riep:
        print('  Aliquota=' + str(extract_tags(r,'AliquotaIVA')) + ' Imponibile=' + str(extract_tags(r,'ImponibileImporto')) + ' IVA=' + str(extract_tags(r,'Imposta')))
    print()
    print('--- PAGAMENTO ---')
    print('CondizioniPagamento:', extract_tags(data, 'CondizioniPagamento'))
    print('ModalitaPagamento:', extract_tags(data, 'ModalitaPagamento'))
    print('DataScadenzaPagamento:', extract_tags(data, 'DataScadenzaPagamento'))
    print('ImportoPagamento:', extract_tags(data, 'ImportoPagamento'))
    print()
