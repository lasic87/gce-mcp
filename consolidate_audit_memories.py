import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_consolidate_memories

async def main():
    summary_content = """
### SOR App (sor-app-v2) - Kompletne Podsumowanie Audytu Bezpieczeństwa IT:
1. **SEC-01 (WebSocket Handshake Auth)**: Wdrożono pakiet AUTH jako warunek konieczny wysłania appState (5s timeout, rozłączenie 4001). Commit 54fbbbb.
2. **SEC-02 (Server-Side Auth)**: Usunięto bcrypt i VITE_PASSW_HASH z frontendu. Dedykowany endpoint HTTP POST /api/login i tokeny sess-<UUID>. Commit 54fbbbb.
3. **SEC-03 (Eliminacja admin123)**: Usunięto hardcodowany token admin123 z całego kodu. Zmiana roli na Administratora/Koordynatora wymaga autoryzacji na backendzie. Commit b33facd.
4. **SEC-04 (Rate Limiting & Capacity Guard)**: Limit 30 akcji/5s per socket WebSocket oraz maksymalna pojemność poczekalni 250 pacjentów (ochrona DoS/OOM). Commit d960138.
5. **SEC-06 (Szyfrowanie bazy AES-256-GCM & chmod 0600)**: Natywne szyfrowanie bazy danych state.json w spoczynku oraz restrykcyjne uprawnienia POSIX mode 0600 / 0700. Dziennik audytowy zdarzeń medycznych odłożony na życzenie użytkownika. Commit b9c83a5.
6. **SEC-07 (Docker Hardening & Pre-compiled Server)**: Skompilowany serwer dist-server/server.js (esbuild) oraz nieuprzywilejowany użytkownik USER node w Dockerfile. Commit d1a393d.
7. **SEC-05 (Caddy Hardening & Security Headers)**: Wdrożono nagłówki bezpieczeństwa HTTP (X-Frame-Options DENY, X-Content-Type-Options nosniff, X-XSS-Protection, Referrer-Policy, Permissions-Policy), wsparcie dla domeny sorbed.szpitalsm.local (tls internal) oraz proxy WebSocket. Commit edf28b3.
8. **Deployment & GitHub**: Wykonano kompilację i wdrożenie na kontenerze Proxmox LXC 151 (192.168.1.153:8088). Wszystkie zmiany wysłane na GitHub (origin-private main, commit 1aa2099).
"""
    print("Consolidating memories via gce_consolidate_memories...")
    try:
        res = await gce_consolidate_memories(content=summary_content, category="sor_app_security_audit_complete")
        print(f"Consolidation Result: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
