import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
  label = "sor_app_sec02_frontend_hash_leak_fixed_2026"
  content = (
      "Rozwiązano podatność SEC-02 (Wyciek hasła w budowanym kodzie frontendu)"
      " w SOR App (sor-app-v2):\n- Wyeliminowano zmienną VITE_PASSW_HASH z"
      " plików .env, .env.example oraz z budowanego kodu klienta klienta"
      " (LoginScreen.tsx).\n- Logowanie przełączono w 100% na backendowy"
      " endpoint HTTP POST /api/login w server.ts, który weryfikuje hasło"
      " przy użyciu bezpiecznej zmiennej środowiskowej serwera"
      " APP_PASSWORD_HASH.\n- Po udanym zalogowaniu serwer generuje bezpieczny,"
      " unikalny token sesji (sess-<UUID>), przesyłany do klienta i używany do"
      " autoryzacji połączenia WebSocket.\n- Z klienta usunięto bibliotekę"
      " bcryptjs, co zmniejszyło rozmiar produkcyjnego bundla JS o ponad 20"
      " kB i uniemożliwiło odczytanie jakichkolwiek haszy z poziomu narzędzi"
      " deweloperskich przeglądarki (F12)."
  )

  print(f"Adding memory with label: {label}...")
  try:
    res = await gce_add_memory(content=content, label=label)
    print(f"Result: {res}")
  except Exception as e:
    print(f"Error: {e}")


if __name__ == "__main__":
  asyncio.run(main())
