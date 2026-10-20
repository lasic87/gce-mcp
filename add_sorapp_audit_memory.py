import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    content = (
        "Audyt Kodu SOR App (SOR-app-v2) - Wnioski i Artefakt (8 sierpnia 2026 r.):\n"
        "- Ścieżka pliku artefaktu z pełnym raportem: /root/.gemini/antigravity-cli/brain/ff2233c3-0693-48c1-b614-72ec13401788/audit_report_sorapp.md\n"
        "- Zainstalowane skille audytowe (globalnie i w workspace): security-auditor, code-reviewer, auth-implementation-patterns, security-scanning-security-sast, security-scanning-security-dependencies, codebase-cleanup-tech-debt, typescript-pro, frontend-security-coder, code-refactoring-refactor-clean.\n"
        "- Kluczowe podatności bezpieczeństwa: Brak uwierzytelniania w połączeniach WebSocket (server.ts), brak sprawdzania ról RBAC przy akcjach WebSocket, brak walidacji i sanitizacji danych pacjentów (ryzyko Stored XSS), wyłączony CSP w Helmet.\n"
        "- Wydajność i współbieżność: Blokujący zapis synchroniczny (fs.writeFileSync) przy każdej akcji WS (należy zmienić na debounced async write), generowanie ID pacjentów przez Date.now() grozi kolizją przy równoległych żądaniach.\n"
        "- Dostępność (WCAG 2.2): Kolory Triage w UI bazują wyłącznie na barwach (wymagane dodanie etykiet tekstowych i priorytetów cyfrowych R1/O2 dla osób z zaburzeniami rozpoznawania barw)."
    )
    label = "sor_app_code_audit_report_2026_08"
    
    print(f"Adding GCE memory with label: {label}...")
    try:
        res = await gce_add_memory(content=content, label=label)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Error saving to GCE: {e}")

if __name__ == "__main__":
    asyncio.run(main())
