import lancedb
import os

DB_PATH = "/root/gce-mcp/data/lancedb"

def main():
    if not os.path.exists(DB_PATH):
        print("Błąd: DB nie istnieje")
        return
    db = lancedb.connect(DB_PATH)
    table = db.open_table("context_store")
    results = table.search().to_list()
    
    with open("all_memories.txt", "w", encoding="utf-8") as f:
        for res in results:
            f.write(f"URI: {res['uri']}\n")
            f.write(f"LABEL: {res.get('abstract', '')}\n")
            f.write(f"TEXT: {res['text']}\n")
            f.write("-" * 40 + "\n")
    print(f"Zapisano {len(results)} rekordów do all_memories.txt")

if __name__ == "__main__":
    main()
