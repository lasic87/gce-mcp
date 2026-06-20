import asyncio
from server import gce_add_memory

async def main():
    content = """* W czerwcu 2026 r. wymieniono fizycznie liczniki wody na nowe modele Apator 162.
* Nowy licznik główny wody ma identyfikator: 0x03669190 (numer seryjny: 3669190).
* Nowy licznik ogrodowy wody ma identyfikator: 0x03864347 (numer seryjny: 3864347).
* Zaktualizowano konfigurację ESPHome wmbus-reader-v5.yaml w Home Assistant o nowe identyfikatory, przeniesiono external_components na oficjalne repozytorium IoTLabs-pl/esphome-components (z zachowaniem jawnej listy modułów: wmbus_common, wmbus_radio, wmbus_meter) oraz włączono poziom logowania DEBUG.
* Procedura aktualizacji sterownika: Przy przejściu ze starego repozytorium SzczepanaLeona na IoTLabs-pl należy najpierw zaktualizować addon ESPHome w HA, przed kompilacją wykonać Clean Build w celu usunięcia starego cache z .esphome, a dopiero potem wgrać oprogramowanie na sterownik."""
    
    label = "wymiana_licznikow_wody_czerwiec_2026"
    print(f"Saving updated memory '{label}' to GCE...")
    result = await gce_add_memory(content, label)
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
