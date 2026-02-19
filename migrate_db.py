"""
Migrazione database: aggiunge le colonne mancanti alla tabella fatture.
Eseguire una volta sola per allineare il DB allo schema attuale.
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
    # Prova a leggere il percorso da column_prefs.json
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

cols = [row[1] for row in cur.execute('PRAGMA table_info(fatture)')]
print('Colonne attuali:', cols)

migrations = [
    ("tipo", "ALTER TABLE fatture ADD COLUMN tipo VARCHAR DEFAULT 'VENDITA'"),
    ("fornitore_codice", "ALTER TABLE fatture ADD COLUMN fornitore_codice VARCHAR"),
    ("fornitore_denominazione", "ALTER TABLE fatture ADD COLUMN fornitore_denominazione VARCHAR"),
]

for col_name, sql in migrations:
    if col_name not in cols:
        cur.execute(sql)
        print(f'Aggiunta colonna: {col_name}')
    else:
        print(f'Colonna già presente: {col_name}')

conn.commit()
print('Migrazione completata.')
print('Colonne dopo migrazione:', [row[1] for row in cur.execute('PRAGMA table_info(fatture)')])
conn.close()
