import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
  label = "sor_app_sec05_caddy_hardening_and_security_headers_fixed_2026"
  content = (
      "Rozwiązano podatność SEC-05 (Wyłączona autoryzacja w Caddy i brak TLS /"
      " Hardening Reverse Proxy) w SOR App (sor-app-v2):\n- Zaktualizowano"
      " Caddyfile: dodano nagłówki bezpieczeństwa HTTP (X-Frame-Options DENY,"
      " X-Content-Type-Options nosniff, X-XSS-Protection 1; mode=block,"
      " Referrer-Policy, Permissions-Policy) oraz ukrycie nagłówka -Server.\n-"
      " Dodano wsparcie dla domeny szpitalnej Paweł (sorbed.szpitalsm.local,"
      " localhost, :8080) z obsługa tls internal.\n- Dodano natywne wsparcie"
      " dla połączeń WebSocket w Caddy proxy (header_up Connection i"
      " Upgrade).\n- Autoryzacja użytkowników i zabezpieczenie danych"
      " realizowane w 100% przez bezpieczny backend Node.js (SEC-01 & SEC-02) bez"
      " potrzeby stosowania surowego popupu Caddy Basic Auth.\n- Zmiany"
      " zweryfikowane testami i utrwalone w komicie Git edf28b3."
  )

  print(f"Adding memory with label: {label}...")
  try:
    res = await gce_add_memory(content=content, label=label)
    print(f"Result: {res}")
  except Exception as e:
    print(f"Error: {e}")


if __name__ == "__main__":
  asyncio.run(main())
