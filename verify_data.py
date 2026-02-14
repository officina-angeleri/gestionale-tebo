from database import DatabaseManager, Cliente, Fornitore, Articolo, RigaVendita

db = DatabaseManager()
session = db.get_session()

print(f"Clienti: {session.query(Cliente).count()}")
print(f"Fornitori: {session.query(Fornitore).count()}")
print(f"Articoli: {session.query(Articolo).count()}")
print(f"Righe Vendita: {session.query(RigaVendita).count()}")

print("\n--- Primi 5 Clienti ---")
for c in session.query(Cliente).limit(5).all():
    print(f"ID: {c.id}, Cod: {c.codice}, RagSoc: {c.ragione_sociale}, Ind: {c.indirizzo}")

print("\n--- Primi 5 Articoli ---")
for a in session.query(Articolo).limit(5).all():
    print(f"ID: {a.id}, Cod: {a.codice}, Desc: {a.descrizione}, Prezzo: {a.prezzo}")
