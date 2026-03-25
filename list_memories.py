import lancedb
db = lancedb.connect("/root/gce-mcp/data/lancedb")
table = db.open_table("context_store")
results = table.search().where("uri LIKE 'gce://user/memories/%'").to_list()
print(f"Liczba wspomnień: {len(results)}")
for res in results:
    print(f"\nURI: {res['uri']}")
    print(f"Abstract: {res['abstract']}")
    print(f"Content: {res['text'][:200]}...")
