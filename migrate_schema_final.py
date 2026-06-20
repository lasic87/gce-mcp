import lancedb
import os
import sys
from pathlib import Path

# Dodaj ścieżkę do modułów GCE
sys.path.append('/root/gce-mcp')
from config import settings

def migrate_schema():
    db_path = settings.GCE_DB_PATH
    print(f"🚀 Starting Database Migration: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ DB path does not exist. Nothing to migrate.")
        return

    try:
        db = lancedb.connect(db_path)
        table_name = "context_store"
        
        # Pobierz listę tabel (używając nowszej metody)
        if table_name not in db.table_names():
            print(f"❌ Table '{table_name}' not found.")
            return

        table = db.open_table(table_name)
        print(f"✅ Opened table '{table_name}'. Current row count: {table.count_rows()}")

        # Pobieramy dane jako listę słowników
        data = table.search().to_list()
        
        if not data:
            print("ℹ️ Table is empty. No migration needed for existing rows.")
            return

        if 'namespace' in data[0]:
            print("ℹ️ Column 'namespace' already exists.")
            return

        print(f"🛠️ Migrating {len(data)} rows to include 'namespace' column...")
        
        # Aktualizacja każdego wiersza
        for row in data:
            row['namespace'] = 'default'
            # Upewniamy się, że metadata to string (LanceDB czasem zwraca słownik)
            if isinstance(row.get('metadata'), dict):
                import json
                row['metadata'] = json.dumps(row['metadata'])
        
        # Nadpisanie tabeli
        # Uwaga: create_table z mode="overwrite" użyje schematu z pierwszego elementu listy
        db.create_table(table_name, data=data, mode="overwrite")
        
        print("✨ Migration successful: 'namespace' column added and data preserved.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_schema()
