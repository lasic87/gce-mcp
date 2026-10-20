import asyncio
from server import gce_add_memory

async def main():
    content = """* W czerwcu 2026 r. utworzono sensor szablonowy `sensor.woda_dom_stan` ("Woda Dom - Stan") w pliku configuration.yaml / templates.yaml.
* Sensor oblicza różnicę między głównym licznikiem wody (`sensor.wmbus_reader_v5_licznik_wody_apator_stan`) a licznikiem ogrodowym (`sensor.wmbus_reader_v5_licznik_wody_ogrod_stan`).
* Służy on do poprawnego rozliczania zużycia wody w domu oraz kosztów ścieków w panelu Energia (Energy Dashboard) w Home Assistant, zapobiegając naliczaniu ścieków dla wody ogrodowej."""
    
    label = "sensor_woda_dom_stan_energia_ha"
    print(f"Saving memory '{label}' to GCE...")
    result = await gce_add_memory(content, label)
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
