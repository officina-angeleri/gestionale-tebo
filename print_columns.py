import pandas as pd

files = [
    "TEBO_ELENCO_ARTICOLI.xls",
    "TEBO_ELENCO_CLIENTI.xls",
    "TEBO_ELENCO_DETTAGLIO_RIGHE_VENDITA.xls",
    "TEBO_ELENCO_FORNITORI.xls"
]

with open("columns.md", "w") as f_out:
    for f in files:
        try:
            df = pd.read_excel(f, nrows=1) 
            f_out.write(f"# {f}\n")
            for col in df.columns:
                f_out.write(f"- {col}\n")
            f_out.write("\n")
        except Exception as e:
            f_out.write(f"Error {f}: {e}\n")
