import lancedb
import sys
import os

# Konfiguracja ścieżki
DB_PATH = "/root/gce-mcp/data/lancedb"

def list_resources(uri_prefix=""):
    if not os.path.exists(DB_PATH):
        print(f"Błąd: Baza danych nie istnieje pod adresem {DB_PATH}")
        return

    db = lancedb.connect(DB_PATH)
    table_name = "context_store"
    
    if table_name not in db.table_names():
        print(f"Błąd: Tabela '{table_name}' nie istnieje w bazie.")
        return

    table = db.open_table(table_name)
    
    # Budowanie zapytania
    query = table.search()
    if uri_prefix:
        query = query.where(f"uri LIKE '{uri_prefix}%'")
    
    results = query.to_list()
    
    print(f"=== GCE RESOURCE LIST ===")
    if uri_prefix:
        print(f"Filtr URI: {uri_prefix}*")
    print(f"Liczba znalezionych rekordów: {len(results)}")
    print("=" * 25)

    for res in results:
        print(f"\nURI: {res['uri']}")
        if res.get('abstract'):
            print(f"LABEL: {res['abstract']}")
        # Wyświetlamy początek tekstu (zastępujemy stare 'content' poprawnym 'text')
        text_preview = res['text'].replace('\n', ' ')[:150]
        print(f"TEXT: {text_preview}...")
        print("-" * 15)

if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else ""
    list_resources(prefix)
