import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import vector_store

async def main():
    target_uri = "gce://user/memories/sor_app_code_audit_report_2026_08"
    try:
        recs = vector_store.table.search().where(f"uri = '{target_uri}'").to_list()
        if not recs:
            print(f"No records found for URI: {target_uri}")
            # Try searching with LIKE
            recs = vector_store.table.search().where("uri LIKE '%sor_app_code_audit%'").to_list()
        
        for r in recs:
            print(f"=== RECORD: {r.get('uri')} ===")
            print(f"Label: {r.get('label')}")
            print(f"Content:\n{r.get('content')}")
            print("="*40)
    except Exception as e:
        print(f"Error fetching record: {e}")

if __name__ == "__main__":
    asyncio.run(main())
