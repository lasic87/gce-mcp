import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
  label = "sor_app_sec01_websocket_auth_handshake_fixed_2026"
  content = (
      "Rozwiązano podatność SEC-01 (WebSocket Data Leak) w SOR App"
      " (sor-app-v2):\n- Wyeliminowano bezpośrednie wysyłanie bazy pacjentów"
      " (appState) przy zdarzeniu wss.on('connection') w server.ts.\n- Wdrożono"
      " serwerowy protokół Handshake Auth: socket zostaje oznaczony jako"
      " isAuthenticated = false, a baza danych jest przesyłana wyłącznie po"
      " odebraniu poprawnego pakietu AUTH { token, role }.\n- Dodano 5-sekundowy"
      " timeout autoryzacji z automatycznym zamykaniem nieautoryzowanych"
      " połączeń (kod 4001).\n- Zaktualizowano App.tsx i LoginScreen.tsx do"
      " obsługi bezpiecznego przechowywania tokenu sesyjnego i przesyłania"
      " pakietu AUTH w locie (w tym obsługa wybudzania po sleeping tabs w"
      " przeglądarce)."
  )

  print(f"Adding memory with label: {label}...")
  try:
    res = await gce_add_memory(content=content, label=label)
    print(f"Result: {res}")
  except Exception as e:
    print(f"Error: {e}")


if __name__ == "__main__":
  asyncio.run(main())
