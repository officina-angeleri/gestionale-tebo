from database import DatabaseManager, Fattura, RigaFattura
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tebo.db")
db = DatabaseManager(db_path)
session = db.get_session()

fatture_count = session.query(Fattura).count()
righe_count = session.query(RigaFattura).count()

print(f"Fatture: {fatture_count}")
print(f"Righe Fattura: {righe_count}")

if fatture_count > 0:
    first_fat = session.query(Fattura).first()
    print(f"Prima Fattura: {first_fat.numero} del {first_fat.data} (Cliente: {first_fat.cliente_codice})")
    print(f"Totale: {first_fat.totale}")
    print(f"Righe collegate: {len(first_fat.righe)}")
    for r in first_fat.righe:
        print(f" - {r.descrizione}: {r.quantita} x {r.prezzo_unitario} = {r.totale_riga}")

session.close()
