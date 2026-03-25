import lancedb
import os
from config import settings
try:
    db_path = "/root/gce-mcp/data/lancedb"
    if os.path.exists(db_path):
        db = lancedb.connect(db_path)
        if "context_store" in db.table_names():
            table = db.open_table("context_store")
            print(f"Liczba fragmentów: {table.count_rows()}")
        else:
            print("Tabela jeszcze nie istnieje.")
    else:
        print("Baza danych nie istnieje.")
except Exception as e:
    print(f"Błąd: {e}")
