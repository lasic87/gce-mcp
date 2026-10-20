import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import gce_add_memory

async def main():
    memories = [
        {
            "label": "ha_waste_collection_schedule_kornik_kiedyodpady",
            "content": "Dla Gminy Kórnik (źródło https://gminakornik.pl/harmonogram-odpadow/) harmonogram wywozu odpadów komunalnych w dodatku 'hacs_waste_collection_schedule' obsługiwany jest bezpośrednio przez wbudowane źródło 'kiedyodpady_pl'. Gmina Kórnik korzysta z instancji platformy Kiedy Odpady pod adresem https://kornik.kiedyodpady.pl/. Konfiguracja wymaga: municipality: 'kornik', city: 'Kórnik (miasto)' (lub odpowiednia miejscowość, np. 'Borówiec (wieś)', 'Kamionki (wieś)'), street: 'ul. Nazwa' oraz number: 'pozostałe'. Pobiera to pełen harmonogram ze wszystkimi frakcjami (Bio, Plastik, Papier, Szkło, Zmieszane)."
        },
        {
            "label": "ha_dashboard_lovelace_waste_card_mushroom",
            "content": "W głównym dashboardzie Home Assistanta (lovelace.lovelace, widok Home, sekcja 'Odpady') wdrożono nowoczesny interfejs wywozu odpadów w architekturze Sections. Składa się z: 1) Dynamicznego banera Mushroom Template Card wyświetlającego stan wywozu na bieżąco (np. '⚠️ JUTRO WYWÓZ! - Wystaw wieczorem: Bio, Segregacja' z pomarańczowym tłem/ikoną lub '🚨 DZISIAJ WYWÓZ!' z czerwonym alertem), oraz 2) Siatki 2x2 kafelków Mushroom dla frakcji (Zmieszane, Segregacja, Bioodpady, Gabaryty). Każdy kafelek prezentuje precyzyjną datę odbioru wyciąganą dynamicznie z atrybutów encji (format %d.%m), liczbę dni, ikony zgodne z kolorystyką kubłów w PL oraz pulsujące/świecące ramki ostrzegawcze card_mod aktywujące się na 0 i 1 dzień przed odbiorem."
        }
    ]
    
    for mem in memories:
        print(f"Adding memory with label: {mem['label']}...")
        try:
            res = await gce_add_memory(content=mem['content'], label=mem['label'])
            print(f"Result for {mem['label']}: {res}")
        except Exception as e:
            print(f"Error for {mem['label']}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
