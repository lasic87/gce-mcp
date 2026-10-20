import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "prowlarr_indexers_cleanup_and_expansion",
            "content": "W dniu 15 sierpnia 2026 r. przeprowadzono naprawę i rozbudowę indexerów w Prowlarr (LXC 101). Usunięto przestarzałe i uszkodzone definicje (TorrentGalaxyClone, Demonoid Clone, ExtraTorrent.st), usuwając błędy w Prowlarr. Dodańo 5 nowych działających publicznych indexerów z podpiętym FlareSolverr (Anibt, CrackingPatching, dmhy, FileMood, GamesTorrents), zwiększając liczbę aktywnych indexerów w Prowlarr do 19."
        }
    ]
    
    for memory in memories:
        print(f"Adding memory with label: {memory['label']}...")
        try:
            res = await gce_add_memory(content=memory['content'], label=memory['label'])
            print(f"Result: {res}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
