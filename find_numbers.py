import re

with open("all_memories.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Szukamy 8-cyfrowych liczb
matches = re.finditer(r'\b\d{8}\b', content)
results = set()

for m in matches:
    num = m.group(0)
    # Wyciągamy kontekst (+- 60 znaków)
    start = max(0, m.start() - 60)
    end = min(len(content), m.end() + 60)
    context = content[start:end].replace('\n', ' ')
    results.add((num, context))

print(f"=== ZNALEZIONE 8-CYFROWE LICZBY ({len(results)} unikalnych) ===")
for num, ctx in sorted(results):
    print(f"{num}: ... {ctx} ...")
