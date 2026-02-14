import pandas as pd
import os

files = [
    "TEBO_ELENCO_ARTICOLI.xls",
    "TEBO_ELENCO_CLIENTI.xls",
    "TEBO_ELENCO_DETTAGLIO_RIGHE_VENDITA.xls",
    "TEBO_ELENCO_FORNITORI.xls"
]

with open("analysis_result.txt", "w") as out:
    for f in files:
        out.write(f"--- {f} ---\n")
        try:
            # Read only header
            df = pd.read_excel(f, nrows=1) 
            out.write(str(df.columns.tolist()) + "\n")
            out.write(str(df.dtypes) + "\n")
        except Exception as e:
            out.write(f"Error reading {f}: {e}\n")
        out.write("\n")
