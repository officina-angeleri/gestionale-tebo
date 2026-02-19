"""
Migrazione database: aggiunge le colonne mancanti alle tabelle fatture e fornitori.
Eseguire ogni volta che lo schema cambia per allineare il DB fisico al modello.
Uso: python migrate_db.py [percorso_db]
     Se non specificato, usa il db_path da column_prefs.json o tebo.db locale.
"""
import sqlite3
import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if len(sys.argv) > 1:
    db_path = sys.argv[1]
else:
    prefs_file = os.path.join(BASE_DIR, 'column_prefs.json')
    if os.path.exists(prefs_file):
        with open(prefs_file, 'r') as f:
            prefs = json.load(f)
        db_path = prefs.get('db_path', os.path.join(BASE_DIR, 'tebo.db'))
    else:
        db_path = os.path.join(BASE_DIR, 'tebo.db')

print(f'Database target: {db_path}')
conn = sqlite3.connect(db_path)
cur = conn.cursor()


def migrate_table(table_name, migrations):
    """Aggiunge colonne mancanti a una tabella."""
    cols = [row[1] for row in cur.execute(f'PRAGMA table_info({table_name})')]
    print(f'\n[{table_name}] Colonne attuali: {cols}')
    for col_name, sql in migrations:
        if col_name not in cols:
            cur.execute(sql)
            print(f'  ✔ Aggiunta colonna: {col_name}')
        else:
            print(f'  · Già presente: {col_name}')


# --- Tabella: fatture ---
migrate_table('fatture', [
    ("tipo",                    "ALTER TABLE fatture ADD COLUMN tipo VARCHAR DEFAULT 'VENDITA'"),
    ("fornitore_codice",        "ALTER TABLE fatture ADD COLUMN fornitore_codice VARCHAR"),
    ("fornitore_denominazione", "ALTER TABLE fatture ADD COLUMN fornitore_denominazione VARCHAR"),
])

# --- Tabella: fornitori ---
migrate_table('fornitori', [
    ("categoria", "ALTER TABLE fornitori ADD COLUMN categoria VARCHAR DEFAULT 'CORE'"),
])

conn.commit()
print('\nMigrazione completata con successo.')
conn.close()
