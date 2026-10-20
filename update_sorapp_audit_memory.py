import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    content = (
        "Audyt Kodu SOR App (SOR-app-v2) - Zaktualizowane Wnioski Runda 2 (8 sierpnia 2026 r.):\n"
        "- Artefakt raportu: /root/.gemini/antigravity-cli/brain/ff2233c3-0693-48c1-b614-72ec13401788/audit_report_sorapp.md\n"
        "- ROZWIAZANE PODATNOSCI (Runda 2):\n"
        "  1. RBAC WebSocket: Dodano socketRoles (WeakMap) i ROLE_PERMISSIONS w server.ts. Zabronione akcje są odrzucane z Access Denied.\n"
        "  2. Sanitizacja danych (XSS): Wdrożono sanitizeText() i sanitizePatientData() dla danych pacjentów.\n"
        "  3. Eliminacja kolizji ID: Zastąpiono Date.now() bezpiecznym crypto.randomUUID().\n"
        "  4. Typowanie TypeScript: Usunięto nieścisły typ 'any'.\n"
        "- POZOSTAŁE REKOMENDACJE DO DALSZEGO ROZWOJU:\n"
        "  1. Zabezpieczenie akcji CHANGE_ROLE po stronie serwera (weryfikacja tokenu/hasła przy zmianie roli na Admin/Coordinator).\n"
        "  2. Optymalizacja I/O: Zmiana synchronicznego fs.writeFileSync na debounced async write w state.json.\n"
        "  3. WCAG: Uzupełnienie oznaczeń Triage o etykiety tekstowe dla daltonistów."
    )
    label = "sor_app_code_audit_report_2026_08"
    
    print(f"Updating GCE memory with label: {label}...")
    try:
        res = await gce_add_memory(content=content, label=label)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error updating GCE: {e}")

if __name__ == "__main__":
    asyncio.run(main())
