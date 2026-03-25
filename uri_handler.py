import os
import re
from pathlib import Path

def generate_uri(file_path: str, base_dir: str = "/root") -> str:
    """
    Konwertuje lokalną ścieżkę do pliku na czytelny URI GCE.
    Przykłady:
    /root/SOR_app/constants.ts -> gce://sor_app/constants.ts
    /root/HA_asystent/config/ha.yaml -> gce://ha_asystent/config/ha.yaml
    """
    try:
        # Rozwiązanie ścieżki absolutnej
        abs_path = Path(file_path).resolve()
        base_path = Path(base_dir).resolve()
        
        # Jeśli ścieżka jest wewnątrz zadanego base_dir, wyciągamy ścieżkę względną
        if abs_path.is_relative_to(base_path):
            rel_path = abs_path.relative_to(base_path)
            # Konwersja na stringa z użyciem slashy unixowych
            path_str = str(rel_path).replace("\\", "/")
        else:
            # W innym przypadku używamy po prostu nazwy pliku lub części oryginalnej ścieżki
            path_str = abs_path.name
        
        # Opcjonalnie: slugify poszczególnych fragmentów, ale dla ścieżek najlepiej zostawić jak są, po prostu małe litery
        slugified_path = path_str.lower()
        
        # Konstrukcja URI
        return f"gce://{slugified_path}"
        
    except Exception as e:
        # Fallback w przypadku błędu
        return f"gce://unknown/{os.path.basename(file_path).lower()}"

def extract_project_name(uri: str) -> str:
    """Wydobywa główny zasób/projekt z URI."""
    match = re.match(r"gce://([^/]+)/", uri)
    if match:
        return match.group(1)
    return "unknown"
