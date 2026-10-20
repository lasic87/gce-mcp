import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import vector_store

async def main():
    print("=== SEARCHING GCE FOR SKILL AUDIT MEMORIES ===")
    try:
        all_recs = vector_store.table.search().to_list()
        print(f"Total records in GCE: {len(all_recs)}")
        
        keywords = ["audit", "audyt", "skill", "security", "code-reviewer", "tech-debt", "vulnerability", "sor_app"]
        
        matches = []
        for r in all_recs:
            uri = str(r.get('uri', ''))
            label = str(r.get('label', ''))
            content = str(r.get('content', ''))
            
            combined_text = f"{uri} {label} {content}".lower()
            
            for kw in keywords:
                if kw in combined_text:
                    matches.append((uri, label, content))
                    break

        print(f"\nFound {len(matches)} matching records:")
        for uri, label, content in matches:
            print("="*60)
            print(f"URI: {uri}")
            print(f"Label: {label}")
            print(f"Content:\n{content}")
            print("="*60)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
