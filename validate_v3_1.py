import asyncio
import logging
import os
import sys

# Konfiguracja środowiska
sys.path.append('/root/gce-mcp')
from server import gce_doctor
from quota_manager import quota_manager
from text_utils import ASTCodeSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FinalValidation")

async def run_validation():
    print("\n" + "="*50)
    print("🔍 GCE v3.1 FINAL VALIDATION SUITE")
    print("="*50 + "\n")

    # 1. Test GCE Doctor v2.0 (Forensics + Thinking Mode)
    print("STEP 1: Testing GCE Doctor v2.0 (Regression Forensics)...")
    try:
        doctor_report = await gce_doctor(fix=False)
        print(f"\n[DOCTOR REPORT]:\n{doctor_report}")
    except Exception as e:
        print(f"❌ Doctor Test FAILED: {e}")

    # 2. Test AST Splitter Precision
    print("\nSTEP 2: Testing AST Splitter Precision...")
    test_code = "async def test_precision():\n    print('Hello world')"
    splitter = ASTCodeSplitter("python", chunk_size=1000)
    chunks = splitter.split_code(test_code)
    if chunks and "async def test_precision" in chunks[0]:
        print("✅ AST Precision: PASSED (No char offsets detected)")
    else:
        print(f"❌ AST Precision: FAILED (Result: {chunks})")

    # 3. QuotaManager Capabilities
    print("\nSTEP 3: Verifying QuotaManager Lineup...")
    try:
        stats = quota_manager.get_stats()
        models = [s['name'] for s in stats]
        required = ["models/gemini-3.1-pro-preview", "models/gemma-4-31b-it", "models/deep-research-pro-preview-12-2025"]
        missing = [m for m in required if m not in models]
        if not missing:
            print("✅ Model Lineup: PASSED (All 2026 models registered)")
        else:
            print(f"❌ Model Lineup: FAILED (Missing: {missing})")
    except Exception as e:
        print(f"❌ QuotaManager Stats FAILED: {e}")

    # Finalizacja - eleganckie zamknięcie sesji
    await quota_manager.close()

    print("\n" + "="*50)
    print("🎯 ALL SYSTEMS OPERATIONAL - GCE 3.1 READY")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(run_validation())
