import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
  label = "sor_app_sec06_aes256_encryption_and_chmod600_fixed_2026"
  content = (
      "Rozwiązano podatność SEC-06 (Nieszyfrowana baza danych i ochrona danych w"
      " spoczynku) w SOR App (sor-app-v2):\n- Wdrożono natywne szyfrowanie"
      " AES-256-GCM dla pliku danych data/state.json w server.ts z kluczem"
      " wyznaczanym z sekretu serwera.\n- Plik danych na dysku zawiera"
      " wyłącznie nieczytelny szyfrogram (cipher, IV, authTag, encrypted"
      " data).\n- Wdrożono automatyczną wsteczną kompatybilność i migrację"
      " starych plików JSON oraz mechanizm bezpiecznego backupu w przypadku"
      " uszkodzenia (state.json.corrupt.<timestamp>).\n- Wdrożono restrykcyjne"
      " uprawnienia systemowe POSIX: mode 0700 dla katalogu data/ oraz mode"
      " 0600 (chmod 600) dla pliku state.json.\n- Dziennik audytowy zdarzeń"
      " medycznych odłożony w czasie na życzenie użytkownika.\n- Zmiany"
      " zweryfikowane testami i utrwalone w komicie Git b9c83a5."
  )

  print(f"Adding memory with label: {label}...")
  try:
    res = await gce_add_memory(content=content, label=label)
    print(f"Result: {res}")
  except Exception as e:
    print(f"Error: {e}")


if __name__ == "__main__":
  asyncio.run(main())
