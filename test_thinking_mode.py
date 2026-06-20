import asyncio
import logging
import os
import sys

# Dodajemy folder gce-mcp do ścieżki
sys.path.append('/root/gce-mcp')

from quota_manager import quota_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ThinkingTest")

async def test_thinking():
    # Ten test wymusza Thinking Mode, co powinno spowodować 
    # przełączenie na model Gemini 2.5 lub 3 w QuotaManager.
    prompt = "Przeanalizuj ostatnie zmiany w GCE (AST, Juggler v3) i wydestyluj 3 najważniejsze korzyści architektoniczne."
    
    logger.info("Starting Thinking Test with Gemini 3/2.5...")
    try:
        response = await quota_manager.generate_content(prompt, thinking=True)
        print(f"\n🚀 **RESPONSE FROM THINKING MODEL:**\n{response}\n")
    except Exception as e:
        logger.error(f"Thinking Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_thinking())
