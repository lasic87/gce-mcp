#!/root/gce-mcp/.venv/bin/python3
import sys
import os
import asyncio

async def index_file(rel_path: str, mode: str):
    # Vault base directory
    vault_base = "/root/vault"
    abs_path = os.path.join(vault_base, rel_path) if not rel_path.startswith("/") else rel_path

    if not abs_path.endswith(".md"):
        return

    if mode == "deleted" or not os.path.exists(abs_path):
        print(f"Skipping deleted file: {abs_path}")
        return

    sys.path.insert(0, "/root/gce-mcp")
    from server import gce_add_resource

    try:
        res = await gce_add_resource(abs_path, namespace="obsidian")
        print(f"GCE Auto-Index [{rel_path}]: {res}")
    except Exception as e:
        print(f"GCE Auto-Index Error for [{rel_path}]: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        action_mode = sys.argv[2] if len(sys.argv) > 2 else "modified"
        asyncio.run(index_file(target_file, action_mode))
