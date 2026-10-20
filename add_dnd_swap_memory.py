import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    label = "sor_app_waiting_list_dnd_swap_modal_2026"
    content = "Zaimplementowano bezpośrednie przeciąganie pacjentów z poczekalni (WaitingList) na kafelki łóżek (BedGrid). W przypadku przeciągnięcia pacjenta na zajęte łóżko wyświetlany jest modal potwierdzenia (ConfirmAssignModal), który pozwala bezpiecznie zamienić pacjentów (przenieść dotychczasowego pacjenta z powrotem do poczekalni i przypisać nowego z poczekalni na łóżko poprzez akcję SWAP_WAITING_TO_OCCUPIED_BED)."
    
    print(f"Adding memory with label: {label}...")
    try:
        res = await gce_add_memory(content=content, label=label)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
