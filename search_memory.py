import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_search_context, vector_store

async def main():
    queries = ["audyt", "audyt kodu", "Paweł", "SOR", "konsultacja IT"]
    print("--- SEARCHING MEMORIES ---")
    for q in queries:
        print(f"\n=== Query: '{q}' ===")
        try:
            res = await gce_search_context(query=q, limit=10)
            print(res)
        except Exception as e:
            print(f"Error for '{q}': {e}")
            
    print("\n--- ALL RECORDS IN TABLE ---")
    try:
        all_recs = vector_store.table.search().to_list()
        for r in all_recs:
            print(f"URI: {r.get('uri')} | Label: {r.get('label')} | Namespace: {r.get('namespace')}")
            content_snippet = str(r.get('content'))[:200].replace('\n', ' ')
            print(f"   Snippet: {content_snippet}\n")
    except Exception as e:
        print(f"Error fetching all: {e}")

if __name__ == "__main__":
    asyncio.run(main())
