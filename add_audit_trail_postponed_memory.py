import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
  label = "sor_app_audit_trail_postponed_decision_2026"
  content = (
      "Decyzja użytkownika dotycząca SEC-06 w SOR App (sor-app-v2):\n- Dziennik"
      " audytowy zdarzeń medycznych (Audit Trail) został na ten moment"
      " odłożony w czasie na życzenie użytkownika.\n- Dane pacjentów mają"
      " charakter tymczasowy (dane w pamięci/pliku roboczym).\n- Funkcja"
      " pełnego dziennika audytowego zostanie rozważona w przyszłych wersjach"
      " produkcyjnych."
  )

  print(f"Adding memory with label: {label}...")
  try:
    res = await gce_add_memory(content=content, label=label)
    print(f"Result: {res}")
  except Exception as e:
    print(f"Error: {e}")


if __name__ == "__main__":
  asyncio.run(main())
