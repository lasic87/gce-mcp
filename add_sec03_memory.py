import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
  label = "sor_app_sec03_hardcoded_admin_token_fixed_2026"
  content = (
      "Rozwiązano podatność SEC-03 (Hardcodowany token administratora admin123"
      " i podatność na eskalację uprawnień) w SOR App (sor-app-v2):\n- Całkowicie"
      " usunięto frazę 'admin123' z kodu serwera (server.ts), frontendu"
      " (App.tsx, Header.tsx) oraz modala (AdminLoginModal.tsx).\n- Akcja"
      " CHANGE_ROLE wymaga teraz podania prawdziwego hasła/tokena"
      " administratora i weryfikacji na backendzie przez verifyAuthToken bez"
      " domyślnego fallbacku.\n- Uniemożliwiono samowolną eskalację uprawnień"
      " przez surowe wiadomości WebSocket.\n- Zmiany zweryfikowane testami"
      " automatycznymi i utrwalone w komicie Git b33facd."
  )

  print(f"Adding memory with label: {label}...")
  try:
    res = await gce_add_memory(content=content, label=label)
    print(f"Result: {res}")
  except Exception as e:
    print(f"Error: {e}")


if __name__ == "__main__":
  asyncio.run(main())
