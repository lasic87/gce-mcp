import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
  label = "sor_app_sec04_rate_limiting_and_capacity_guard_2026"
  content = (
      "Rozwiązano podatność SEC-04 (Brak walidacji wielkości żądań i brak Rate"
      " Limitingu - Podatność DoS) w SOR App (sor-app-v2):\n- Wdrożono"
      " ogranicznik częstotliwości żądań (Rate Limiting) w server.ts: max 30"
      " akcji w oknie 5 sekund na jedno połączenie WebSocket. Przekroczenie"
      " limitu zwraca błąd 'Zbyt wysoka częstotliwość żądań'.\n- Ustawiono sztywny"
      " limit pojemności poczekalni (Capacity Guard) na maksymalnie 250"
      " pacjentów (zgodnie z wymogami operacyjnymi użytkownika). Próba dodania"
      " 251. pacjenta jest odrzucana z komunikatem o przepełnieniu"
      " poczekalni.\n- Zabezpieczono serwer i kontener Proxmox przed wyczerpaniem"
      " pamięci RAM (OOM Killer) i zapchaniem I/O dysku przez ataki typu"
      " DoS/spam.\n- Zmiany zweryfikowane testami i utrwalone w komicie Git"
      " d960138."
  )

  print(f"Adding memory with label: {label}...")
  try:
    res = await gce_add_memory(content=content, label=label)
    print(f"Result: {res}")
  except Exception as e:
    print(f"Error: {e}")


if __name__ == "__main__":
  asyncio.run(main())
