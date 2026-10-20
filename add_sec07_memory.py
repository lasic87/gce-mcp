import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
  label = "sor_app_sec07_docker_unprivileged_user_and_compiled_server_fixed_2026"
  content = (
      "Rozwiązano podatność SEC-07 (Kontener uruchamiany jako root z narzędziem"
      " tsx) w SOR App (sor-app-v2):\n- Zbudowano produkcyjną, samodzielną"
      " kompilację serwera Node.js ES module (dist-server/server.js) przy"
      " użyciu esbuild. Zastąpiono kompilację w locie 'npx tsx server.ts'"
      " bezpośrednim uruchamianiem 'node dist-server/server.js'.\n- Dodano"
      " skrypty build:server oraz automatyczną kompilację serwera podczas npm"
      " run build.\n- Zaktualizowano Dockerfile i start.sh: utworzono katalogi"
      " robocze z chown -R node:node oraz przełączono kontener na"
      " nieuprzywilejowanego użytkownika USER node zamiast root.\n- Zmiany"
      " zweryfikowane testami i utrwalone w komicie Git d1a393d."
  )

  print(f"Adding memory with label: {label}...")
  try:
    res = await gce_add_memory(content=content, label=label)
    print(f"Result: {res}")
  except Exception as e:
    print(f"Error: {e}")


if __name__ == "__main__":
  asyncio.run(main())
