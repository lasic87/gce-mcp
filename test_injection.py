import asyncio
from embedding_engine import embedding_engine
from vector_store import vector_store

async def test():
    print("=== TEST INJECTION (LanceDB Direct) ===")
    
    test_text = "To jest testowy kontekst o asystencie Homelab GCE, sprawdzający spójność kolumn."
    test_uri = "gce://test/consistency_check"
    
    print(f"1. Generating embedding for: {test_uri}")
    vector = await embedding_engine.embed_text(test_text)
    print(f"   Vector generated, length: {len(vector)}")
    
    print("2. Saving to LanceDB (using 'text' and 'abstract' columns)...")
    doc = {
        "uri": test_uri,
        "text": test_text,
        "abstract": "Testowy abstrakt spójności",
        "vector": vector,
        "metadata": "{'source': 'test_injection'}"
    }
    vector_store.add_documents([doc])
    
    print("3. Searching LanceDB using hybrid search...")
    # Szukamy słów, które są w abstrakcie, aby sprawdzić nowy indeks FTS
    results = vector_store.hybrid_search(
        query="abstrakt spójności", 
        query_vector=vector, 
        limit=1
    )
    
    if results:
        print(f"   Found URI: {results[0]['uri']}")
        print(f"   Text: {results[0]['text'][:50]}...")
        print(f"   Abstract: {results[0]['abstract']}")
        print("\n✅ Test spójności zakończony pomyślnie.")
    else:
        print("❌ Nie znaleziono wyników.")

if __name__ == "__main__":
    asyncio.run(test())
