import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import vector_store

async def main():
    print("=== INSPECTING LANCEDB SCHEMA AND DATA ===")
    try:
        tbl = vector_store.table
        print("Schema fields:", tbl.schema.names)
        
        # Target URI search
        records = tbl.search().where("uri LIKE '%audit%'").to_list()
        for r in records:
            print("\n--- FOUND RECORD ---")
            for key, val in r.items():
                if val and key != 'vector':
                    print(f"  {key}: {str(val)[:300]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
