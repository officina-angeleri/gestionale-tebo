import pandas as pd
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "TEBO_ELENCO_DETTAGLIO_RIGHE_VENDITA.xls")

if os.path.exists(file_path):
    df = pd.read_excel(file_path, nrows=5)
    print("Columns:", df.columns.tolist())
    print("First 3 rows:")
    print(df.head(3).to_string())
else:
    print(f"File not found: {file_path}")
