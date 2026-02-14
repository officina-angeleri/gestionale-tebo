import pandas as pd
import json

files = [
    "TEBO_ELENCO_ARTICOLI.xls",
    "TEBO_ELENCO_CLIENTI.xls",
    "TEBO_ELENCO_DETTAGLIO_RIGHE_VENDITA.xls",
    "TEBO_ELENCO_FORNITORI.xls"
]

schemas = {}
for f in files:
    try:
        # Read only header
        df = pd.read_excel(f, nrows=1) 
        schemas[f] = df.columns.tolist()
    except Exception as e:
        schemas[f] = str(e)

with open("schema.json", "w") as out:
    json.dump(schemas, out, indent=2)
