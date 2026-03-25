import asyncio
from embedding_engine import embedding_engine
from vector_store import vector_store

async def test():
    print("Testing embedding...")
    vector = await embedding_engine.embed_text("To jest testowy kontekst o asystencie Homelab GCE.")
    print(f"Vector generated, length: {len(vector)}")
    print("Saving to LanceDB...")
    vector_store.add_document("gce://test/homelab.txt", "To jest testowy kontekst o asystencie Homelab GCE.", vector)
    print("Searching LanceDB...")
    results = vector_store.search(vector, limit=1)
    print(f"Found: {results[0]['uri']}")

asyncio.run(test())
