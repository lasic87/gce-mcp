import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    label = "sor_app_triage_pink_status_2026"
    content = "Dodano nowy kolor statusu Triage w SOR App - kolor różowy ('pink') dedykowany dla pacjentów ze statusem 'Wypis / Przyjęcie'. Został dodany do typów TriageColor, stylów Tailwind w BedTile i WaitingList oraz formularzy dodawania/edycji pacjenta (NewPatientForm, PatientModal)."
    
    print(f"Adding memory with label: {label}...")
    try:
        res = await gce_add_memory(content=content, label=label)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
