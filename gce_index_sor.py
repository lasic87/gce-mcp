import asyncio
from pathlib import Path
from server import gce_add_resource

async def index_sor():
    # Folder projektu SOR App
    project_dir = "/root/SOR_app"
    extensions = ['.ts', '.tsx', '.css', '.html', '.json', '.md', '.py']
    
    print(f"Scanning {project_dir} for SOR App code...")
    path = Path(project_dir)
    count = 0
    
    for file in path.rglob('*'):
        if file.is_file() and file.suffix in extensions:
            if 'node_modules' in str(file) or 'dist' in str(file) or '.git' in str(file) or '.next' in str(file):
                continue
            
            print(f"Indexing: {file}")
            result = await gce_add_resource(str(file))
            if "Sukces" in result:
                count += 1
                
    print(f"Finished. Indexed {count} files from SOR App.")

if __name__ == "__main__":
    asyncio.run(index_sor())
